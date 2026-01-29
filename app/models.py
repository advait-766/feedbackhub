from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

def create_user(username, password, role="user"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, generate_password_hash(password), role)
    )
    conn.commit()
    conn.close()

def authenticate(username, password):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash, role FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row[1], password):
        return {"id": row[0], "role": row[2]}
    return None
