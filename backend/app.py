from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib

app = Flask(__name__)
CORS(app)  # Allow frontend requests

DB_NAME = "database.db"

# Helper function to connect DB
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

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
    address = data.get('address')
    fees = data.get('fees')

    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash password

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO students (name, email, password, center, address, fees)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, hashed_password, center, address, fees))
        conn.commit()
        return jsonify({'message': 'Student registered successfully!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Email already exists!'}), 400
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
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE email = ? AND password = ?', (email, hashed_password))
    student = cursor.fetchone()
    conn.close()

    if student:
        return jsonify({'message': 'Login successful!', 'student': dict(student)}), 200
    else:
        return jsonify({'message': 'Invalid email or password!'}), 401

# -----------------------------
# Admin Login (Fixed)
# -----------------------------
@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, hashed_password))
    admin = cursor.fetchone()
    conn.close()

    if admin:
        return jsonify({'message': 'Admin login successful!', 'admin': dict(admin)}), 200
    else:
        return jsonify({'message': 'Invalid username or password!'}), 401

# -----------------------------
# Get all students (for admin)
# -----------------------------
@app.route('/get_students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, center, address, fees FROM students')
    students = cursor.fetchall()
    conn.close()
    return jsonify([dict(s) for s in students]), 200

# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)