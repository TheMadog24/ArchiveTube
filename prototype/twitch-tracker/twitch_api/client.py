import json
import logging
import sqlite3
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from database.db import record_api_usage

logger = logging.getLogger(__name__)

TOKEN_URL = "https://id.twitch.tv/oauth2/token"

# Cached app access token
_cached_token = None


def get_app_access_token(client_id, client_secret):
    """Request an app access token from Twitch."""

    global _cached_token

    # Reuse the cached token if one exists
    if _cached_token:
        return _cached_token

    if not client_id or not client_secret:
        raise RuntimeError(
            "Twitch Client ID or Client Secret is missing. Check your configuration."
        )

    data = urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
    ).encode("utf-8")

    request = Request(
        TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            token_data = json.loads(response.read().decode("utf-8"))

        # Store the token for reuse
        _cached_token = token_data["access_token"]

        return _cached_token

    except HTTPError as error:
        raise RuntimeError(
            f"Twitch authentication failed (HTTP {error.code}). "
            "Check your Twitch application credentials."
        ) from error

    except URLError as error:
        raise RuntimeError(f"Could not connect to Twitch: {error.reason}") from error


def clear_app_access_token():
    """Clear the cached app access token."""
    global _cached_token
    _cached_token = None


API_BASE_URL = "https://api.twitch.tv/helix"


def helix_request(endpoint, client_id, client_secret, params=None):
    """Send an authenticated GET request to the Twitch Helix API."""

    # Build the API URL
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

    if params:
        url = f"{url}?{urlencode(params)}"

    # Convert the endpoint into a safe, predefined category.
    endpoint_path = endpoint.strip("/").lower()

    if endpoint_path.startswith("eventsub/subscriptions"):
        endpoint_category = "eventsub_subscriptions"
    else:
        endpoint_category = endpoint_path.split("/")[0]

    allowed_endpoints = {
        "users",
        "streams",
        "games",
        "channels",
        "videos",
        "eventsub_subscriptions",
    }

    if endpoint_category not in allowed_endpoints:
        endpoint_category = "other"

    def log_usage(status_code, duration_ms, headers=None):
        """Record aggregate usage without affecting the API request."""

        headers = headers or {}

        def header_integer(name):
            try:
                return int(headers[name])
            except (KeyError, TypeError, ValueError):
                return None

        try:
            record_api_usage(
                endpoint=endpoint_category,
                status_code=status_code,
                duration_ms=duration_ms,
                rate_limit_limit=header_integer("ratelimit-limit"),
                rate_limit_remaining=header_integer("ratelimit-remaining"),
                rate_limit_reset=header_integer("ratelimit-reset"),
            )

        except sqlite3.Error:
            # Never expose database error details.
            logger.warning("Could not record Twitch API usage statistics.")

    # Allow one retry if Twitch rejects our access token.
    for attempt in range(2):
        token = get_app_access_token(client_id, client_secret)

        request = Request(
            url,
            headers={
                "Client-ID": client_id,
                "Authorization": f"Bearer {token}",
            },
            method="GET",
        )

        start_time = perf_counter()

        try:
            with urlopen(request, timeout=15) as response:
                response_data = json.loads(response.read().decode("utf-8"))

                duration_ms = round((perf_counter() - start_time) * 1000)

                response_headers = {
                    key.lower(): value for key, value in response.headers.items()
                }

                log_usage(
                    response.status,
                    duration_ms,
                    response_headers,
                )

                return response_data, response_headers

        except HTTPError as error:
            duration_ms = round((perf_counter() - start_time) * 1000)

            error_headers = (
                {key.lower(): value for key, value in error.headers.items()}
                if error.headers
                else {}
            )

            log_usage(
                error.code,
                duration_ms,
                error_headers,
            )

            # If the token is invalid, get a new one and retry once.
            if error.code == 401 and attempt == 0:
                clear_app_access_token()
                continue

            raise RuntimeError(
                f"Twitch API request failed (HTTP {error.code})."
            ) from error

        except TimeoutError as error:
            duration_ms = round((perf_counter() - start_time) * 1000)

            log_usage(None, duration_ms)

            raise TimeoutError("Twitch API request timed out.") from error

        except URLError as error:
            duration_ms = round((perf_counter() - start_time) * 1000)

            log_usage(None, duration_ms)

            raise RuntimeError("Could not connect to Twitch.") from error

    raise RuntimeError("Twitch API request failed after refreshing the access token.")
