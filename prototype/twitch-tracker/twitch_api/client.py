
import json
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen



TOKEN_URL = "https://id.twitch.tv/oauth2/token"


def get_app_access_token(client_id, client_secret):
    """Request an app access token from Twitch."""

    if not client_id or not client_secret:
        raise RuntimeError(
            "Twitch Client ID or Client Secret is missing. "
            "Check your configuration."
        )

    data = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }).encode("utf-8")

    request = Request(
        TOKEN_URL,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST"
    )

    try:
        with urlopen(request, timeout=15) as response:
            token_data = json.loads(response.read().decode("utf-8"))

        return token_data

    except HTTPError as error:
        raise RuntimeError(
            f"Twitch authentication failed (HTTP {error.code}). "
            "Check your Twitch application credentials."
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Could not connect to Twitch: {error.reason}"
        ) from error
        