from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash
from db import init_db, get_db
from models import authenticate_user, create_user
from captcha import generate_captcha

app = Flask(__name__)
app.secret_key = "college-demo-secret"

# -----------------------------
# INITIALIZATION
# -----------------------------
init_db()

def ensure_admin_exists():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE role='admin'")
    admin = cur.fetchone()

    if not admin:
        cur.execute("""
            INSERT INTO users (username, password_hash, role, is_initialized)
            VALUES (?, ?, 'admin', 0)
        """, ("admin", generate_password_hash("admin@123")))
        conn.commit()

    conn.close()

ensure_admin_exists()

# -----------------------------
# CONSTANTS
# -----------------------------
SUBJECTS = [
    "Fundamentals of Computer Networks",
    "Operating Systems & Administration",
    "Security Concepts",
    "Network Defense & Countermeasures",
    "DevOps & Cloud Computing"
]

RATINGS = ["Not Satisfied", "Satisfied", "Very Satisfied", "Perfect"]

# -----------------------------
# AUTH ROUTES
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    captcha_text = generate_captcha()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        captcha_input = request.form.get("captcha")

        if captcha_input != session.get("captcha"):
            error = "Invalid CAPTCHA"
        else:
            user = authenticate_user(username, password)
            if user:
                session["user_id"] = user["id"]
                session["role"] = user["role"]

                # Log login
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO login_logs (user_id) VALUES (?)",
                    (user["id"],)
                )
                conn.commit()
                conn.close()

                return redirect("/admin" if user["role"] == "admin" else "/feedback")
            else:
                error = "Invalid credentials"

    session["captcha"] = captcha_text
    return render_template("auth/login.html", error=error, captcha=captcha_text)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error = "All fields are required"
        else:
            try:
                create_user(username, password)
                return redirect("/")
            except Exception:
                error = "Username already exists"

    return render_template("auth/register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -----------------------------
# USER FEEDBACK (PROGRESSIVE)
# -----------------------------
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user_id" not in session or session.get("role") != "user":
        return redirect("/")

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    # Completed subjects
    cur.execute("SELECT subject FROM feedback WHERE user_id = ?", (user_id,))
    completed = {row[0] for row in cur.fetchall()}

    # Next subject
    next_subject = None
    for subject in SUBJECTS:
        if subject not in completed:
            next_subject = subject
            break

    if not next_subject:
        conn.close()
        return render_template("user/feedback_done.html")

    if request.method == "POST":
        cur.execute("""
            INSERT INTO feedback (user_id, subject, rating, comments)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            next_subject,
            request.form["rating"],
            request.form.get("comments", "")
        ))
        conn.commit()
        conn.close()
        return redirect("/feedback")

    conn.close()
    return render_template(
        "user/feedback.html",
        subject=next_subject,
        ratings=RATINGS
    )

# -----------------------------
# ADMIN ROUTES (ENTERPRISE UI)
# -----------------------------
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    # Basic stats
    cur.execute("SELECT COUNT(*) FROM users WHERE role='user'")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM feedback")
    total_feedback = cur.fetchone()[0]

    stats = []
    for r in RATINGS:
        cur.execute("SELECT COUNT(*) FROM feedback WHERE rating = ?", (r,))
        stats.append(cur.fetchone()[0])

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_feedback=total_feedback,
        feedbackStats=stats
    )

@app.route("/admin/users")
def admin_users():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, role, password_hash FROM users")
    rows = cur.fetchall()
    conn.close()

    users = [
        {"username": r[0], "role": r[1], "password_hash": r[2]}
        for r in rows
    ]

    return render_template("admin/users.html", users=users)


@app.route("/admin/feedback")
def admin_feedback():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username, f.subject, f.rating
        FROM feedback f
        JOIN users u ON u.id = f.user_id
        ORDER BY f.timestamp DESC
    """)
    rows = cur.fetchall()
    conn.close()

    feedback = [
        {
            "username": r[0],
            "subject": r[1],
            "rating": r[2],
            "completed": True
        }
        for r in rows
    ]

    return render_template("admin/feedback.html", feedback=feedback)


@app.route("/admin/logs")
def admin_logs():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username, l.login_time
        FROM login_logs l
        JOIN users u ON u.id = l.user_id
        ORDER BY l.login_time DESC
    """)
    rows = cur.fetchall()
    conn.close()

    logs = [{"username": r[0], "time": r[1]} for r in rows]

    return render_template("admin/logs.html", logs=logs)

# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
