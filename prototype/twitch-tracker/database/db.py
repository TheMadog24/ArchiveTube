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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                twitch_user_id TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL,
                display_name TEXT NOT NULL,
                profile_image_url TEXT,
                tracking_enabled INTEGER NOT NULL DEFAULT 0,
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

        # Store long-term daily API usage summaries.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS api_usage_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_utc TEXT NOT NULL,
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
                UNIQUE(date_utc, endpoint)
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


def get_api_usage_summary():
    """Return overall Twitch API usage statistics."""

    connection = get_connection()

    try:
        row = connection.execute("""
            WITH all_usage AS (
                SELECT
                    request_count,
                    success_count,
                    failure_count,
                    unauthorized_count,
                    rate_limited_count,
                    total_duration_ms,
                    max_duration_ms
                FROM api_usage

                UNION ALL

                SELECT
                    request_count,
                    success_count,
                    failure_count,
                    unauthorized_count,
                    rate_limited_count,
                    total_duration_ms,
                    max_duration_ms
                FROM api_usage_daily
            )
            SELECT
                COALESCE(SUM(request_count), 0) AS total_requests,
                COALESCE(SUM(success_count), 0) AS successful_requests,
                COALESCE(SUM(failure_count), 0) AS failed_requests,
                COALESCE(SUM(unauthorized_count), 0)
                    AS unauthorized_requests,
                COALESCE(SUM(rate_limited_count), 0)
                    AS rate_limited_requests,
                COALESCE(SUM(total_duration_ms), 0)
                    AS total_duration_ms,
                MAX(max_duration_ms) AS max_duration_ms
            FROM all_usage
        """).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_api_usage_by_endpoint(period="24h"):
    """Return Twitch API usage grouped by endpoint for a selected period."""

    valid_periods = ("24h", "7d", "30d", "12m", "all")

    if period not in valid_periods:
        raise ValueError("Invalid time period.")

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            WITH all_usage AS (
                SELECT
                    endpoint,
                    minute_utc AS usage_time,
                    request_count,
                    success_count,
                    failure_count,
                    total_duration_ms,
                    max_duration_ms
                FROM api_usage

                UNION ALL

                SELECT
                    endpoint,
                    date_utc AS usage_time,
                    request_count,
                    success_count,
                    failure_count,
                    total_duration_ms,
                    max_duration_ms
                FROM api_usage_daily
            )
            SELECT
                endpoint,
                SUM(request_count) AS total_requests,
                SUM(success_count) AS successful_requests,
                SUM(failure_count) AS failed_requests,
                SUM(total_duration_ms) AS total_duration_ms,
                MAX(max_duration_ms) AS max_duration_ms
            FROM all_usage
            WHERE
                CASE
                    WHEN ? = '24h'
                        THEN usage_time >= strftime('%Y-%m-%dT%H:%MZ', 'now', '-24 hours')
                    WHEN ? = '7d'
                        THEN usage_time >= strftime('%Y-%m-%dT%H:%MZ', 'now', '-7 days')
                    WHEN ? = '30d'
                        THEN usage_time >= strftime('%Y-%m-%d', 'now', '-30 days')
                    WHEN ? = '12m'
                        THEN usage_time >= strftime('%Y-%m-%d', 'now', '-12 months')
                    ELSE 1
                END
            GROUP BY endpoint
            ORDER BY total_requests DESC
        """,
            (period, period, period, period),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_api_usage_history(period="24h", endpoint=None):
    """Return API usage history grouped into appropriate time buckets."""

    valid_periods = {"24h", "7d", "30d", "12m", "all"}

    if period not in valid_periods:
        raise ValueError("Invalid API usage history period.")

    connection = get_connection()

    try:
        if period == "24h":
            query = """
                SELECT
                    minute_utc AS period,
                    SUM(request_count) AS total_requests,
                    SUM(success_count) AS successful_requests,
                    SUM(failure_count) AS failed_requests,
                    SUM(total_duration_ms) AS total_duration_ms
                FROM api_usage
                WHERE minute_utc >= strftime(
                    '%Y-%m-%dT%H:%MZ',
                    'now',
                    '-24 hours'
                )
            """

            parameters = []

            if endpoint is not None:
                query += " AND endpoint = ?"
                parameters.append(endpoint)

            query += """
                GROUP BY minute_utc
                ORDER BY minute_utc ASC
            """

        else:
            if period == "7d":
                cutoff = "-7 days"
                bucket = "%Y-%m-%dT%H"
            elif period == "30d":
                cutoff = "-30 days"
                bucket = "%Y-%m-%d"
            elif period == "12m":
                cutoff = "-12 months"
                bucket = "%Y-%m-%d"
            else:
                cutoff = None
                bucket = "%Y-%m-%d"

            query = """
                WITH all_usage AS (
                    SELECT
                        minute_utc AS recorded_at,
                        endpoint,
                        request_count,
                        success_count,
                        failure_count,
                        total_duration_ms
                    FROM api_usage

                    UNION ALL

                    SELECT
                        date_utc AS recorded_at,
                        endpoint,
                        request_count,
                        success_count,
                        failure_count,
                        total_duration_ms
                    FROM api_usage_daily
                )
                SELECT
                    strftime(?, recorded_at) AS period,
                    SUM(request_count) AS total_requests,
                    SUM(success_count) AS successful_requests,
                    SUM(failure_count) AS failed_requests,
                    SUM(total_duration_ms) AS total_duration_ms
                FROM all_usage
            """

            parameters = [bucket]

            if cutoff is not None:
                query += """
                    WHERE recorded_at >= strftime('%Y-%m-%dT%H:%MZ', 'now', ?)
                """
                parameters.append(cutoff)

            if endpoint is not None:
                query += (
                    " AND endpoint = ?" if cutoff is not None else " WHERE endpoint = ?"
                )
                parameters.append(endpoint)

            query += """
                GROUP BY period
                ORDER BY period ASC
            """

        rows = connection.execute(query, parameters).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_api_rate_limit_history(hours=24):
    """Return rate-limit information over a time period."""

    if not isinstance(hours, int) or isinstance(hours, bool) or hours < 1:
        raise ValueError("Hours must be a positive integer.")

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                minute_utc,
                MIN(min_rate_limit_remaining) AS remaining,
                MAX(rate_limit_limit) AS rate_limit,
                MAX(rate_limit_reset) AS reset_timestamp
            FROM api_usage
            WHERE minute_utc >= strftime(
                '%Y-%m-%dT%H:%MZ',
                'now',
                ?
            )
            AND min_rate_limit_remaining IS NOT NULL
            GROUP BY minute_utc
            ORDER BY minute_utc ASC
        """,
            (f"-{hours} hours",),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def archive_old_api_usage(days):
    """Move old minute-level API usage into daily summaries."""

    if not isinstance(days, int) or isinstance(days, bool) or days < 1:
        raise ValueError("Days must be a positive integer.")

    connection = get_connection()

    try:
        # Start a transaction so archiving and deletion happen together.
        connection.execute("BEGIN IMMEDIATE")

        # Find older records and group them by UTC date and endpoint.
        rows = connection.execute(
            """
            SELECT
                date(minute_utc) AS date_utc,
                endpoint,
                SUM(request_count) AS request_count,
                SUM(success_count) AS success_count,
                SUM(failure_count) AS failure_count,
                SUM(unauthorized_count) AS unauthorized_count,
                SUM(rate_limited_count) AS rate_limited_count,
                SUM(total_duration_ms) AS total_duration_ms,
                MAX(max_duration_ms) AS max_duration_ms,
                MIN(min_rate_limit_remaining)
                    AS min_rate_limit_remaining,
                MAX(rate_limit_limit) AS rate_limit_limit
            FROM api_usage
            WHERE minute_utc < strftime(
                '%Y-%m-%dT%H:%MZ',
                'now',
                ?
            )
            GROUP BY date(minute_utc), endpoint
            """,
            (f"-{days} days",),
        ).fetchall()

        # Save the daily summaries.
        for row in rows:
            connection.execute(
                """
                INSERT INTO api_usage_daily (
                    date_utc,
                    endpoint,
                    request_count,
                    success_count,
                    failure_count,
                    unauthorized_count,
                    rate_limited_count,
                    total_duration_ms,
                    max_duration_ms,
                    min_rate_limit_remaining,
                    rate_limit_limit
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(date_utc, endpoint)
                DO UPDATE SET
                    request_count = request_count + excluded.request_count,
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
                    rate_limit_limit = MAX(
                        rate_limit_limit,
                        excluded.rate_limit_limit
                    )
                """,
                tuple(row),
            )

        # Delete minute-level records only after summaries are saved.
        connection.execute(
            """
            DELETE FROM api_usage
            WHERE minute_utc < strftime(
                '%Y-%m-%dT%H:%MZ',
                'now',
                ?
            )
            """,
            (f"-{days} days",),
        )

        connection.commit()

        return len(rows)

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


def add_channel(
    twitch_user_id,
    username,
    display_name,
    profile_image_url=None,
):
    """Add a Twitch channel to the ArchiveTube library."""

    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO channels (
                twitch_user_id,
                username,
                display_name,
                profile_image_url,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(twitch_user_id) DO NOTHING
            """,
            (
                twitch_user_id,
                username,
                display_name,
                profile_image_url,
                now,
                now,
            ),
        )

        connection.commit()

        return cursor.rowcount == 1

    finally:
        connection.close()


def get_channels():
    """Return all channels in the ArchiveTube library."""

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                twitch_user_id,
                username,
                display_name,
                profile_image_url,
                tracking_enabled,
                created_at,
                updated_at
            FROM channels
            ORDER BY display_name COLLATE NOCASE ASC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_channel(channel_id):
    """Return a single channel from the ArchiveTube library."""

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                twitch_user_id,
                username,
                display_name,
                profile_image_url,
                tracking_enabled,
                created_at,
                updated_at
            FROM channels
            WHERE id = ?
            """,
            (channel_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def remove_channel(channel_id):
    """Remove a channel from the ArchiveTube library."""

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM channels
            WHERE id = ?
            """,
            (channel_id,),
        )

        connection.commit()

        return cursor.rowcount == 1

    finally:
        connection.close()
