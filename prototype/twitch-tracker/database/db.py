import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Database location
DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = DATABASE_DIR / "archivetube.db"


def get_connection():
    """Create a connection to the ArchiveTube database."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the database and its initial tables."""

    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tracked_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                twitch_user_id TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL,
                display_name TEXT NOT NULL,
                profile_image_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Remove the old individual-request log table.
        # It contains no useful data yet.

        # Store aggregated API usage instead of individual requests.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                minute_utc TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                request_count INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                failure_count INTEGER NOT NULL DEFAULT 0,
                unauthorized_count INTEGER NOT NULL DEFAULT 0,
                rate_limited_count INTEGER NOT NULL DEFAULT 0,
                total_duration_ms INTEGER NOT NULL DEFAULT 0,
                max_duration_ms INTEGER,
                min_rate_limit_remaining INTEGER,
                rate_limit_limit INTEGER,
                rate_limit_reset INTEGER,
                UNIQUE(minute_utc, endpoint)
            )
        """)

        connection.commit()

    finally:
        connection.close()


def record_api_usage(
    endpoint,
    status_code,
    duration_ms,
    rate_limit_limit=None,
    rate_limit_remaining=None,
    rate_limit_reset=None,
):
    """Aggregate Twitch API usage by minute and endpoint."""

    # Only accept predefined endpoint labels.
    allowed_endpoints = {
        "users",
        "streams",
        "games",
        "channels",
        "videos",
        "eventsub_subscriptions",
        "other",
    }

    if endpoint not in allowed_endpoints:
        raise ValueError("Unrecognized API endpoint category.")

    # Round the timestamp down to the current UTC minute.
    minute_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    success = status_code is not None and 200 <= status_code < 300
    unauthorized = status_code == 401
    rate_limited = status_code == 429
    failure = not success

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO api_usage (
                minute_utc,
                endpoint,
                request_count,
                success_count,
                failure_count,
                unauthorized_count,
                rate_limited_count,
                total_duration_ms,
                max_duration_ms,
                min_rate_limit_remaining,
                rate_limit_limit,
                rate_limit_reset
            )
            VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(minute_utc, endpoint)
            DO UPDATE SET
                request_count = request_count + 1,
                success_count = success_count + excluded.success_count,
                failure_count = failure_count + excluded.failure_count,
                unauthorized_count = unauthorized_count
                    + excluded.unauthorized_count,
                rate_limited_count = rate_limited_count
                    + excluded.rate_limited_count,
                total_duration_ms = total_duration_ms
                    + excluded.total_duration_ms,
                max_duration_ms = MAX(
                    max_duration_ms,
                    excluded.max_duration_ms
                ),
                min_rate_limit_remaining = CASE
                    WHEN excluded.min_rate_limit_remaining IS NULL
                    THEN min_rate_limit_remaining
                    WHEN min_rate_limit_remaining IS NULL
                    THEN excluded.min_rate_limit_remaining
                    ELSE MIN(
                        min_rate_limit_remaining,
                        excluded.min_rate_limit_remaining
                    )
                END,
                rate_limit_limit = COALESCE(
                    excluded.rate_limit_limit,
                    rate_limit_limit
                ),
                rate_limit_reset = COALESCE(
                    excluded.rate_limit_reset,
                    rate_limit_reset
                )
            """,
            (
                minute_utc,
                endpoint,
                int(success),
                int(failure),
                int(unauthorized),
                int(rate_limited),
                duration_ms or 0,
                duration_ms,
                rate_limit_remaining,
                rate_limit_limit,
                rate_limit_reset,
            ),
        )

        connection.commit()

    finally:
        connection.close()
