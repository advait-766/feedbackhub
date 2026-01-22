import sqlite3

DB_NAME = "feedback.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    print("[DB] Recreating database schema...")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS feedback")
    cur.execute("DROP TABLE IF EXISTS login_logs")

    cur.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        is_initialized INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        rating TEXT,
        comments TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        login_time DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

    print("[DB] Schema recreated successfully")

