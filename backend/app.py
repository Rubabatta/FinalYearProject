from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

DB_NAME = "database.db"

# -----------------------------
# Database Connection
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# Home Route
# -----------------------------
@app.route('/')
def home():
    return "🚀 Uni Shuttle Server Running"

# -----------------------------
# Student Signup
# -----------------------------
@app.route('/student_signup', methods=['POST'])
def student_signup():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    center = data.get('center')
    studentID = data.get('studentID')  # ✅ changed from address
    contact = data.get('contact')
    fees = data.get('fees')

    conn = get_db_connection()
    cursor = conn.cursor()

    # StudentID unique check
    cursor.execute("SELECT * FROM students WHERE studentID=?", (studentID,))  # ✅ changed
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return jsonify({"message":"Student ID already exists"}),400

    try:
        cursor.execute("""
            INSERT INTO students (name,email,password,center,studentID,contact,fees)
            VALUES (?,?,?,?,?,?,?)
        """, (name,email,password,center,studentID,contact,fees))

        conn.commit()

        return jsonify({"message":"Student registered successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"message":"Email already exists"}), 400

    finally:
        conn.close()

# -----------------------------
# Student Login
# -----------------------------
@app.route('/student_login', methods=['POST'])
def student_login():

    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE email=? AND password=?",
        (email,password)
    )

    student = cursor.fetchone()

    conn.close()

    if student:
        return jsonify({
            "message":"Login successful",
            "student":dict(student)
        })
    else:
        return jsonify({"message":"Invalid email or password"}), 401

# -----------------------------
# Admin Login
# -----------------------------
@app.route('/admin_login', methods=['POST'])
def admin_login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM admins WHERE username=? AND password=?",
        (username,password)
    )

    admin = cursor.fetchone()

    conn.close()

    if admin:
        return jsonify({
            "message":"Admin login successful",
            "admin":dict(admin)
        })
    else:
        return jsonify({"message":"Invalid username or password"}), 401

# -----------------------------
# Get Students
# -----------------------------
@app.route('/get_students', methods=['GET'])
def get_students():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
        id,
        name,
        email,
        studentID,
        center,
        contact,
        password,
        fees
        FROM students
    """)

    students = cursor.fetchall()

    conn.close()

    return jsonify([dict(s) for s in students])

# -----------------------------
# Add Student (Admin)
# -----------------------------
@app.route('/add_student', methods=['POST'])
def add_student():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    studentID = data.get("studentID")
    center = data.get("center")
    contact = data.get("contact")
    password = data.get("password")
    fees = data.get("fees",0)

    conn = get_db_connection()
    cursor = conn.cursor()

    # StudentID unique check
    cursor.execute("SELECT * FROM students WHERE studentID=?", (studentID,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return jsonify({"message":"Student ID already exists"}),400

    try:

        cursor.execute("""
            INSERT INTO students
            (name,email,studentID,center,contact,password,fees)
            VALUES (?,?,?,?,?,?,?)
        """,
        (name,email,studentID,center,contact,password,fees))

        conn.commit()

        return jsonify({"message":"Student added successfully"})

    except sqlite3.IntegrityError:

        return jsonify({"message":"Email already exists"}),400

    finally:

        conn.close()

# -----------------------------
# Update Student
# -----------------------------
@app.route('/update_student/<int:student_id>', methods=['PUT'])
def update_student(student_id):

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    studentID = data.get("studentID")
    center = data.get("center")
    contact = data.get("contact")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE students
        SET
        name=?,
        email=?,
        studentID=?,
        center=?,
        contact=?,
        password=?
        WHERE id=?
    """,
    (name,email,studentID,center,contact,password,student_id))

    conn.commit()

    conn.close()

    return jsonify({"message":"Student updated successfully"})

# -----------------------------
# Delete Student
# -----------------------------
@app.route('/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id=?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({"message":"Student deleted successfully"})

# -----------------------------
# Search Students
# -----------------------------
@app.route('/search_students', methods=['GET'])
def search_students():

    query = request.args.get("q","").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
        id,
        name,
        email,
        studentID,
        center,
        contact,
        password,
        fees
        FROM students
        WHERE
        name LIKE ?
        OR email LIKE ?
        OR studentID LIKE ?
        OR center LIKE ?
        OR contact LIKE ?
    """,
    (f"%{query}%",
     f"%{query}%",
     f"%{query}%",
     f"%{query}%",
     f"%{query}%"))

    students = cursor.fetchall()

    conn.close()

    return jsonify([dict(s) for s in students])

# -----------------------------
# Get Single Student
# -----------------------------
@app.route('/get_student/<int:student_id>', methods=['GET'])
def get_student(student_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
        id,
        name,
        email,
        studentID,
        center,
        contact,
        password,
        fees
        FROM students
        WHERE id=?
    """,(student_id,))

    student = cursor.fetchone()

    conn.close()

    if student:
        return jsonify(dict(student))
    else:
        return jsonify({"message":"Student not found"})

# -----------------------------
# Run Server
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)