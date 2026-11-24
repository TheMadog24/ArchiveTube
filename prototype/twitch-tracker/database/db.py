
import sqlite3
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

        connection.commit()

    finally:
        connection.close()
