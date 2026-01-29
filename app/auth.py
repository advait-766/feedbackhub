from functools import wraps
from flask import session, redirect

def login_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if "user_id" not in session:
            return redirect("/")
        return f(*a, **k)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if session.get("role") != "admin":
            return redirect("/dashboard")
        return f(*a, **k)
    return wrap
