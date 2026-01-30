from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash
from datetime import datetime
import sqlite3
import csv
import io
from flask import Response
from flask import Flask, render_template, request, redirect, session, jsonify, url_for, Response
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.security import generate_password_hash
import json
# ... rest of your imports
# Local imports
from models import authenticate, create_user
from captcha import generate_captcha
from courses import COURSES, FEEDBACK_METRICS

DB_NAME = "feedbackhub.db"
app = Flask(__name__)
app.secret_key = "fortinet-style-secure-key-2026"

metrics = PrometheusMetrics(app, group_by='endpoint')
metrics.info('app_info', 'FeedbackHub DevSecOps Portal', version='1.0.0')

# --- DEVSECOPS SECURITY LAYERS ---
csrf = CSRFProtect(app)
csp = {
    'default-src': '\'self\'',
    'script-src': [
        '\'self\'',
        'https://cdn.jsdelivr.net',
        'https://cdn.tailwindcss.com'
    ],
    'style-src': [
        '\'self\'',
        'https://cdn.tailwindcss.com',
        '\'unsafe-inline\''
    ]
}
Talisman(app, content_security_policy=csp)

# =====================================================
# CDAC FEEDBACK FLOW (WITH MONITORING)
# =====================================================

@app.route("/feedback/<course_id>/<module_code>", methods=["GET", "POST"])
# This custom metric will show up in Grafana as a "Feedback Counter"
@metrics.counter('feedback_submissions_total', 'Total feedback forms submitted')
def module_feedback(course_id, module_code):
    if "user_id" not in session:
        return redirect("/")

    course = COURSES.get(course_id)
    module = next((m for m in course["modules"] if m["code"] == module_code), None)

    if request.method == "POST":
        metrics_data = {m: request.form.get(f"metric_{m}") for m in FEEDBACK_METRICS}
        
        conn = get_db()
        conn.execute("""
            INSERT INTO feedback (user_id, course, module_code, module_title, rating, metrics_json, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"], 
            course_id, 
            module_code, 
            module["title"], 
            request.form.get("rating", 5), 
            json.dumps(metrics_data), 
            request.form.get("comments", "")
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('course_modules', course_id=course_id))

    return render_template("user/module_feedback.html", 
                           course=course, 
                           module=module, 
                           metrics=FEEDBACK_METRICS)
# --- DEVSECOPS SECURITY LAYERS ---
csrf = CSRFProtect(app)
# Content Security Policy (Fortinet-like strictness)
csp = {
    'default-src': '\'self\'',
    'script-src': [
        '\'self\'',
        'https://cdn.jsdelivr.net', # For Chart.js
        'https://cdn.tailwindcss.com'
    ],
    'style-src': [
        '\'self\'',
        'https://cdn.tailwindcss.com',
        '\'unsafe-inline\'' # For Tailwind dynamic colors
    ]
}
Talisman(app, content_security_policy=csp)

# -------------------- DATABASE INIT --------------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        created_at TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course TEXT,
        module_code TEXT,
        module_title TEXT,
        rating INTEGER,
        metrics_json TEXT, -- Stores granular ratings for CDAC metrics
        comments TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        login_time DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    # Auto-admin provisioning
    cur.execute("SELECT id FROM users WHERE role='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                    ("admin", generate_password_hash("Admin@123"), "admin", datetime.now().isoformat()))
    conn.commit()
    conn.close()

init_db()

# =====================================================
# AUTHENTICATION
# =====================================================

@app.route("/", methods=["GET", "POST"])
def login():
    if "captcha" not in session:
        session["captcha"] = generate_captcha()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        captcha_input = request.form.get("captcha", "").upper()

        if captcha_input != session.get("captcha", ""):
            return render_template("auth/login.html", error="Invalid CAPTCHA", captcha=session["captcha"])
        
        user = authenticate(username, password)
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            
            # Log successful access (SIEM Simulation)
            conn = get_db()
            conn.execute("INSERT INTO login_logs (user_id) VALUES (?)", (user["id"],))
            conn.commit()
            conn.close()

            return redirect("/admin" if user["role"] == "admin" else "/dashboard")
        
        session["captcha"] = generate_captcha()
        return render_template("auth/login.html", error="Access Denied: Invalid Credentials", captcha=session["captcha"])

    return render_template("auth/login.html", captcha=session.get("captcha"))

# =====================================================
# CDAC FEEDBACK FLOW
# =====================================================

# --- USER DASHBOARD ---
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    # Redirect admins to their specific console if they land here
    if session.get("role") == "admin":
        return redirect("/admin")
    return render_template("user/dashboard.html")

# --- COURSE SELECTION ---
@app.route("/select-course", methods=["GET", "POST"])
def select_course():
    if "user_id" not in session:
        return redirect("/")
        
    if request.method == "POST":
        course_id = request.form.get("course")
        return redirect(url_for('course_modules', course_id=course_id))

    return render_template("user/select_course.html", courses=COURSES)

# --- MODULE LISTING ---
@app.route("/course/<course_id>")
def course_modules(course_id):
    if "user_id" not in session:
        return redirect("/")

    course = COURSES.get(course_id)
    if not course:
        return redirect("/select-course")

    # Renders the page showing modules like 'Advanced Java', 'DBT', etc.
    return render_template("user/course_modules.html", 
                           course_id=course_id, 
                           course=course)

# --- FEEDBACK FORM SUBMISSION ---
@app.route("/feedback/<course_id>/<module_code>", methods=["GET", "POST"])
def module_feedback(course_id, module_code):
    if "user_id" not in session:
        return redirect("/")

    course = COURSES.get(course_id)
    module = next((m for m in course["modules"] if m["code"] == module_code), None)

    if request.method == "POST":
        import json
        # Capture granular CDAC metrics
        metrics_data = {m: request.form.get(f"metric_{m}") for m in FEEDBACK_METRICS}
        
        conn = get_db()
        conn.execute("""
            INSERT INTO feedback (user_id, course, module_code, module_title, rating, metrics_json, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"], 
            course_id, 
            module_code, 
            module["title"], 
            request.form.get("rating", 5), 
            json.dumps(metrics_data), 
            request.form.get("comments", "")
        ))
        conn.commit()
        conn.close()
        # Redirect back to module list after successful submission
        return redirect(url_for('course_modules', course_id=course_id))

    return render_template("user/module_feedback.html", 
                           course=course, 
                           module=module, 
                           metrics=FEEDBACK_METRICS)

# =====================================================
# ADMIN (SEC-OPS PORTAL)
# =====================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            error = "All fields are required."
        else:
            try:
                # Security: default role is always 'user'
                create_user(username, password) 
                return redirect(url_for('login'))
            except Exception as e:
                # Usually happens if username is taken (Unique constraint)
                error = "Identity ID already exists in the system."
                
    return render_template("auth/register.html", error=error)
    
import csv
import io
from flask import Response

# --- GRAPHICAL DATA HELPER ---
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin": 
        return redirect("/")
    
    conn = get_db()
    
    # 1. Gather Metric Statistics for the top cards
    stats = {
        "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "feedback": conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0],
        "logins": conn.execute("SELECT COUNT(*) FROM login_logs").fetchone()[0],
        "courses": len(COURSES)  # Assuming COURSES is imported from courses.py
    }

    # 2. Graphical Data: Avg Rating per Module
    chart_data = conn.execute("""
        SELECT module_title, AVG(rating) as avg_r 
        FROM feedback GROUP BY module_title LIMIT 5
    """).fetchall()
    
    # 3. Graphical Data: Feedback count per Course
    course_data = conn.execute("""
        SELECT course, COUNT(*) as count 
        FROM feedback GROUP BY course
    """).fetchall()
    
    # 4. Recent Telemetry (Optional but looks good on the dashboard)
    recent_feedback = conn.execute("""
        SELECT u.username, f.course, f.module_title, f.rating, f.timestamp 
        FROM feedback f JOIN users u ON u.id = f.user_id 
        ORDER BY f.timestamp DESC LIMIT 5
    """).fetchall()
    
    conn.close()

    return render_template("admin/dashboard.html",
        stats=stats,
        labels=[row['module_title'] for row in chart_data],
        values=[row['avg_r'] for row in chart_data],
        course_labels=[row['course'] for row in course_data],
        course_counts=[row['count'] for row in course_data],
        recent_feedback=recent_feedback
    )

# --- SECURE DOWNLOAD FEATURE ---
@app.route("/admin/export/feedback")
def export_feedback():
    if session.get("role") != "admin": 
        return "Access Denied", 403
    
    conn = get_db()
    cursor = conn.execute("""
        SELECT u.username, f.course, f.module_title, f.rating, f.comments, f.timestamp 
        FROM feedback f JOIN users u ON u.id = f.user_id
    """)
    
    # Create an in-memory string buffer
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write Header
    writer.writerow(['Student_ID', 'Course', 'Module', 'Rating', 'Comments', 'Timestamp'])
    
    # Write Data
    for row in cursor.fetchall():
        writer.writerow(row)
    
    conn.close()
    
    # Secure stream response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=CDAC_Feedback_Audit.csv"}
    )
# --- IDENTITY MANAGEMENT ---
# --- IDENTITY MANAGEMENT ---
@app.route("/admin/users")
def route_admin_users():
    if session.get("role") != "admin": 
        return redirect("/")
    conn = get_db()
    # Fetch all users for the Identity Management table
    users = conn.execute("SELECT id, username, role, created_at FROM users").fetchall()
    conn.close()
    return render_template("admin/users.html", users=users)

# --- ACCESS SIEM (LOGS) ---
@app.route("/admin/logins")
def route_admin_logins():
    if session.get("role") != "admin": 
        return redirect("/")
    conn = get_db()
    # Join users and logs to show who logged in and when
    logs = conn.execute("""
        SELECT u.username, l.login_time 
        FROM login_logs l
        JOIN users u ON u.id = l.user_id 
        ORDER BY l.login_time DESC
    """).fetchall()
    conn.close()
    return render_template("admin/logins.html", logs=logs)
# --- FEEDBACK LOGS ---
@app.route("/admin/feedback")
def admin_feedback_list():
    if session.get("role") != "admin": return redirect("/")
    
    conn = get_db()
    feedbacks = conn.execute("""
        SELECT u.username, f.course, f.module_title, 
               f.rating, f.comments, f.timestamp 
        FROM feedback f
        JOIN users u ON u.id = f.user_id
        ORDER BY f.timestamp DESC
    """).fetchall()
    conn.close()
    return render_template("admin/feedback_list.html", feedbacks=feedbacks)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
