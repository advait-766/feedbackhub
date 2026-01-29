from db import get_db
from models import create_user

conn = get_db()

# admin
try:
    create_user("admin", "admin123", "admin")
except:
    pass

courses = ["PG-DITISS", "PG-DAC"]
modules = {
    "PG-DITISS": ["OS", "Networks", "Security", "Cloud"],
    "PG-DAC": ["C", "DSA", "Java", "DBMS"]
}

for c in courses:
    conn.execute("INSERT INTO courses (name) VALUES (?)", (c,))

conn.commit()

for c in conn.execute("SELECT * FROM courses"):
    for m in modules[c["name"]]:
        conn.execute(
            "INSERT INTO modules (course_id, name) VALUES (?, ?)",
            (c["id"], m)
        )

conn.commit()
conn.close()
print("Seeded successfully")
