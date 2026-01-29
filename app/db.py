import sqlite3
from pathlib import Path

DB_PATH = Path("feedbackhub.db")

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
	    id INTEGER PRIMARY KEY AUTOINCREMENT,
	    user_id INTEGER,
	    course TEXT,
	    module_code TEXT,
	    module_title TEXT,
	    rating TEXT,
	    comments TEXT,
	    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     )
     """)


    conn.commit()
    conn.close()
