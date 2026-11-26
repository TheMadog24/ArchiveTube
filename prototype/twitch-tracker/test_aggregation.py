
from database.db import get_connection

connection = get_connection()

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
        rate_limit_limit
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        "2020-01-01T12:00Z",
        "streams",
        5,
        4,
        1,
        0,
        0,
        500,
        150,
        750,
        800,
    ),
)

connection.commit()
connection.close()

print("Temporary test record inserted.")
