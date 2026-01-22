from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

def authenticate_user(username, password):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, password_hash, role, is_initialized FROM users WHERE username = ?",
        (username,)
    )
    user = cur.fetchone()

    if not user:
        conn.close()
        return None

    user_id, pwd_hash, role, initialized = user

    # 🔓 First-time admin login (no auth)
    if role == "admin" and initialized == 0:
        cur.execute(
            "UPDATE users SET is_initialized = 1 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()
        return {"id": user_id, "role": role}

    # 🔐 Normal authentication
    if pwd_hash and check_password_hash(pwd_hash, password):
        conn.close()
        return {"id": user_id, "role": role}

    conn.close()
    return None
def create_user(username, password):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (username, password_hash, role, is_initialized) VALUES (?, ?, 'user', 1)",
        (username, generate_password_hash(password))
    )

    conn.commit()
    conn.close()


