
import json
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Database and manifest locations
BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "database" / "archivetube.db"
MANIFEST_FILE = BASE_DIR / "test_chart_data_manifest.json"

# Test data settings
ENDPOINTS = ["users", "streams", "games", "channels"]
RANDOM_SEED = 42


def generate_request_count(rng, endpoint, index, total_points):
    """Generate varied request counts for an endpoint."""

    # Different baseline levels make the lines easier to distinguish.
    baselines = {
        "users": 2,
        "streams": 8,
        "games": 3,
        "channels": 5,
    }

    baseline = baselines[endpoint]

    # Gradual waves, occasional spikes, and quiet periods.
    wave = int(5 * (1 + __import__("math").sin(index / 5)))
    variation = rng.randint(-3, 5)

    if rng.random() < 0.08:
        variation += rng.randint(8, 20)

    if rng.random() < 0.12:
        variation -= rng.randint(1, 4)

    return max(0, baseline + wave + variation)


def create_test_data():
    """Insert synthetic chart data without overwriting existing records."""

    if MANIFEST_FILE.exists():
        print("A test-data manifest already exists.")
        print("Clean up the previous test data before generating more.")
        return

    rng = random.Random(RANDOM_SEED)
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    connection = sqlite3.connect(DATABASE_FILE)

    inserted_records = []

    try:
        # Generate one point every 15 minutes for the last 24 hours.
        # Generate one point every hour for the previous 6 days.
        # Generate one point per day for the previous 11 months.
        time_points = set()

        for minutes_ago in range(0, 24 * 60, 15):
            time_points.add(now - timedelta(minutes=minutes_ago))

        for hours_ago in range(24, 7 * 24):
            time_points.add(now - timedelta(hours=hours_ago))

        for days_ago in range(7, 365):
            time_points.add(now - timedelta(days=days_ago))

        time_points = sorted(time_points)

        for endpoint in ENDPOINTS:
            for index, timestamp in enumerate(time_points):
                minute_utc = timestamp.strftime("%Y-%m-%dT%H:%MZ")

                # Do not overwrite existing API usage.
                existing = connection.execute(
                    """
                    SELECT 1
                    FROM api_usage
                    WHERE minute_utc = ? AND endpoint = ?
                    """,
                    (minute_utc, endpoint),
                ).fetchone()

                if existing:
                    continue

                request_count = generate_request_count(
                    rng,
                    endpoint,
                    index,
                    len(time_points),
                )

                success_count = request_count
                failure_count = 0

                if request_count > 0 and rng.random() < 0.08:
                    failure_count = 1
                    success_count -= 1

                total_duration_ms = request_count * rng.randint(80, 350)

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
                    VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, ?, 800, NULL)
                    """,
                    (
                        minute_utc,
                        endpoint,
                        request_count,
                        success_count,
                        failure_count,
                        total_duration_ms,
                        rng.randint(100, 500),
                        rng.randint(650, 799),
                    ),
                )

                inserted_records.append({
                    "minute_utc": minute_utc,
                    "endpoint": endpoint,
                })

        connection.commit()

        # Save exactly which rows this script inserted.
        MANIFEST_FILE.write_text(
            json.dumps(inserted_records, indent=4),
            encoding="utf-8",
        )

        print(f"Inserted {len(inserted_records)} synthetic records.")
        print(f"Manifest saved to: {MANIFEST_FILE}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    create_test_data()
