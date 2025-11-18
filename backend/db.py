from pathlib import Path
import sqlite3
from datetime import datetime

# db/webguard.db relative to project root
DB_PATH = Path(__file__).parent.parent / "db" / "webguard.db"


def init_db():
    # Make sure db folder exists
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        checked_at TEXT NOT NULL,
        status_code INTEGER,
        is_up INTEGER,
        response_time REAL,
        ssl_ok INTEGER,
        ssl_days_left INTEGER,
        error TEXT
    );
    """)
    conn.commit()
    conn.close()


def insert_check(url, status_code, is_up, response_time,
                 ssl_ok, ssl_days_left, error):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO checks (
            url, checked_at, status_code, is_up, response_time,
            ssl_ok, ssl_days_left, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url,
        datetime.utcnow().isoformat(),
        status_code,
        1 if is_up else 0,
        response_time,
        None if ssl_ok is None else (1 if ssl_ok else 0),
        ssl_days_left,
        error
    ))
    conn.commit()
    conn.close()
