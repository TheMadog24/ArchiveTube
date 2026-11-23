import getpass
import json
import socket
import ssl
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
OUTPUT_DIR = BASE_DIR / "output"

SERVER = "irc.chat.twitch.tv"
PORT = 6697

# Maximum time to wait for incoming data before detecting a stalled
# connection. This does not mean the stream has ended.
SOCKET_TIMEOUT = 180


def utc_now():
    """Return the current UTC time with millisecond precision."""
    return datetime.now(timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def create_capture_filename():
    """Create a unique filename for this capture run."""
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d_%H-%M-%S_%f"
    )
    return OUTPUT_DIR / f"twitch_capture_{timestamp}.jsonl"


def load_config():
    """Load and validate the channel and account username."""
    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = json.load(file)

    channel = config["channel"].strip().lower().lstrip("#")
    username = config["username"].strip().lower()

    if not channel or not username:
        raise ValueError("Channel and username cannot be empty.")

    return channel, username


def write_record(log, record):
    """Write one JSONL record and explicitly flush it."""
    log.write(
        json.dumps(record, ensure_ascii=False) + "\n"
    )
    log.flush()


def write_event(log, event, **details):
    """Record a collector lifecycle event."""
    record = {
        "received_at": utc_now(),
        "source": "collector",
        "event": event,
    }
    record.update(details)
    write_record(log, record)


def is_authentication_failure(line):
    """Recognize common Twitch IRC authentication failures."""
    lower_line = line.lower()

    known_messages = (
        "login authentication failed",
        "login unsuccessful",
        "improperly formatted auth",
        "authentication failed",
    )

    if any(message in lower_line for message in known_messages):
        return True

    # IRC numeric 464 is ERR_PASSWDMISMATCH.
    parts = line.split()
    if len(parts) > 1 and parts[1] == "464":
        return True

    return False


def main():
    try:
        channel, username = load_config()
    except (
        OSError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
    ) as exc:
        print(f"Could not load config.json: {exc}")
        return

    token = getpass.getpass(
        "Enter your Twitch OAuth access token (input hidden): "
    ).strip()

    if token.lower().startswith("oauth:"):
        token = token[6:]

    if not token:
        print("No token entered. Exiting.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create a new filename for every run; never append to an old run.
    output_file = create_capture_filename()

    print(f"Channel: #{channel}")
    print(f"Raw capture: {output_file}")
    print("Connecting to Twitch IRC...")

    context = ssl.create_default_context()
    end_reason = "unknown"
    auth_failed = False
    joined = False
    buffer = b""

    try:
        # Open the file before connecting so connection failures are logged.
        with output_file.open(
            "x", encoding="utf-8", buffering=1
        ) as log:
            write_event(
                log,
                "capture_started",
                channel=channel,
                username=username,
            )

            try:
                write_event(
                    log,
                    "connection_attempt",
                    server=SERVER,
                    port=PORT,
                )

                with socket.create_connection(
                    (SERVER, PORT), timeout=20
                ) as raw:
                    with context.wrap_socket(
                        raw, server_hostname=SERVER
                    ) as sock:
                        sock.settimeout(SOCKET_TIMEOUT)

                        write_event(
                            log,
                            "tls_connected",
                            server=SERVER,
                            port=PORT,
                        )

                        def send_irc(message):
                            # Only allow protocol/authentication setup,
                            # channel joining, and keepalive responses.
                            command = message.split(" ", 1)[0].upper()
                            allowed = {
                                "PASS", "NICK", "CAP", "JOIN", "PONG"
                            }

                            if command not in allowed:
                                raise ValueError(
                                    "Blocked unsupported IRC command."
                                )

                            sock.sendall(
                                (message + "\r\n").encode("utf-8")
                            )

                        send_irc(f"PASS oauth:{token}")
                        send_irc(f"NICK {username}")
                        send_irc(
                            "CAP REQ :twitch.tv/membership "
                            "twitch.tv/tags twitch.tv/commands"
                        )

                        print(
                            "Connected to the server. "
                            "Waiting for authentication..."
                        )
                        print("Press Ctrl+C to stop the capture.")

                        while True:
                            chunk = sock.recv(4096)

                            if not chunk:
                                end_reason = "server_closed_connection"
                                write_event(
                                    log,
                                    "connection_closed",
                                    reason=end_reason,
                                )
                                print("Twitch closed the connection.")
                                break

                            buffer += chunk

                            while b"\r\n" in buffer:
                                raw_line, buffer = buffer.split(
                                    b"\r\n", 1
                                )

                                if not raw_line:
                                    continue

                                line = raw_line.decode(
                                    "utf-8", errors="replace"
                                )

                                # Preserve every complete incoming IRC line.
                                write_record(
                                    log,
                                    {
                                        "received_at": utc_now(),
                                        "source": "irc",
                                        "raw": line,
                                    },
                                )

                                # Handle protocol keepalive requests.
                                if line.startswith("PING "):
                                    send_irc("PONG " + line[5:])

                                # Detect authentication errors.
                                if is_authentication_failure(line):
                                    auth_failed = True
                                    end_reason = "authentication_failed"

                                    write_event(
                                        log,
                                        "authentication_failed",
                                    )

                                    print(
                                        "Authentication failed. "
                                        "Check the token and account username."
                                    )
                                    break

                                # Wait for Twitch's welcome numeric before
                                # joining the channel.
                                parts = line.split()

                                if (
                                    not joined
                                    and len(parts) > 1
                                    and parts[1] == "001"
                                ):
                                    write_event(
                                        log,
                                        "irc_authenticated",
                                    )

                                    send_irc(f"JOIN #{channel}")
                                    joined = True

                                    write_event(
                                        log,
                                        "join_requested",
                                        channel=channel,
                                    )

                                    print(
                                        "IRC authentication accepted. "
                                        f"Joining #{channel}..."
                                    )

                                # JOIN confirmation is logged only when
                                # Twitch sends a JOIN line from our username.
                                if (
                                    joined
                                    and line.startswith(
                                        f":{username}!".lower()
                                    )
                                    and f" JOIN #{channel}" in line.upper()
                                ):
                                    write_event(
                                        log,
                                        "channel_join_confirmed",
                                        channel=channel,
                                    )
                                    print(f"Joined #{channel}.")

                                # Show received lines for live inspection.
                                print(line)

                            if auth_failed:
                                break

            except KeyboardInterrupt:
                end_reason = "stopped_by_user"
                print("\nCapture stopped by user.")

            except (OSError, ssl.SSLError) as exc:
                end_reason = (
                    "connection_timeout"
                    if isinstance(exc, socket.timeout)
                    else "connection_error"
                )

                write_event(
                    log,
                    "connection_error",
                    error_type=type(exc).__name__,
                    error=str(exc),
                )

                print(f"\nConnection error: {exc}")

            finally:
                write_event(
                    log,
                    "capture_ended",
                    reason=end_reason,
                    authentication_failed=auth_failed,
                    channel_joined=joined,
                )

    except OSError as exc:
        print(f"\nCould not create or write the capture file: {exc}")

    finally:
        # Never print or save the OAuth token.
        token = None
        print(f"Collector finished. Capture file: {output_file}")


if __name__ == "__main__":
    main()