from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # Frontend se cross-origin requests allow karne ke liye

# ==============================
# DATABASE CONNECTION
# ==============================
def get_db_connection():
    conn = sqlite3.connect('database.db')  # database.db automatically backend folder me banegi
    conn.row_factory = sqlite3.Row
    return conn

# ==============================
# DATABASE INITIALIZATION
# ==============================
def init_db():
    conn = get_db_connection()

    # Shuttle Location Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS shuttle_location (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Users Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database & tables ready!")

# ==============================
# HOME ROUTE
# ==============================
@app.route('/')
def home():
    return "✅ Shuttle Tracking Backend Running"

# ==============================
# GET SHUTTLE LOCATION (Student)
# ==============================
@app.route('/get_location')
def get_location():
    conn = get_db_connection()
    shuttle = conn.execute(
        'SELECT * FROM shuttle_location ORDER BY id DESC LIMIT 1'
    ).fetchone()
    conn.close()

    if shuttle:
        return jsonify({
            "latitude": shuttle["latitude"],
            "longitude": shuttle["longitude"],
            "timestamp": shuttle["timestamp"]
        })
    return jsonify({"error": "No data available"})

# ==============================
# UPDATE LOCATION (Driver)
# ==============================
@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        return jsonify({"error": "Missing data"}), 400

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO shuttle_location (latitude, longitude) VALUES (?,?)",
        (latitude, longitude)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "Location Updated"})

# ==============================
# CREATE TEST USERS
# ==============================
@app.route('/create_test_users')
def create_users():
    conn = get_db_connection()
    users = [
        ("driver", "123", "driver"),
        ("student", "123", "student"),
        ("admin", "123", "admin")
    ]
    for user in users:
        try:
            conn.execute(
                "INSERT INTO users (username,password,role) VALUES (?,?,?)",
                user
            )
        except:
            pass  # avoid duplicate error
    conn.commit()
    conn.close()
    return "✅ Test Users Created"

# ==============================
# LOGIN ROUTE
# ==============================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()

    if user:
        return jsonify({
            "status": "success",
            "role": user["role"]
        })

    return jsonify({"status": "invalid"}), 401

# ==============================
# ADD TEST LOCATION (Optional)
# ==============================
@app.route('/add_test_location')
def add_test_location():
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO shuttle_location (latitude, longitude) VALUES (?,?)",
        (24.8607, 67.0011)
    )
    conn.commit()
    conn.close()
    return "✅ Test Location Added"

# ==============================
# RUN SERVER
# ==============================
if __name__ == '__main__':
    init_db()
    app.run(debug=False)