from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)  # ✅ fix CORS

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
    address = data.get('address')
    fees = data.get('fees')

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO students (name,email,password,center,address,fees)
            VALUES (?,?,?,?,?,?)
        """, (name,email,hashed_password,center,address,fees))
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
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE email=? AND password=?", (email,hashed_password))
    student = cursor.fetchone()
    conn.close()

    if student:
        return jsonify({"message":"Login successful","student":dict(student)})
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
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username=? AND password=?", (username,hashed_password))
    admin = cursor.fetchone()
    conn.close()

    if admin:
        return jsonify({"message":"Admin login successful","admin":dict(admin)})
    else:
        return jsonify({"message":"Invalid username or password"}), 401

# -----------------------------
# Get Students
# -----------------------------
@app.route('/get_students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id,name,email,center,address,fees FROM students")
    students = cursor.fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

# -----------------------------
# Get Buses
# -----------------------------
@app.route('/get_buses', methods=['GET'])
def get_buses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id,bus_number,route_id FROM buses")
    buses = cursor.fetchall()
    conn.close()
    return jsonify([dict(b) for b in buses])

# -----------------------------
# Add Bus
# -----------------------------
@app.route('/add_bus', methods=['POST'])
def add_bus():
    data = request.get_json()
    bus_number = data.get("bus_number")
    route_id = data.get("route_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO buses (bus_number,route_id) VALUES (?,?)", (bus_number,route_id))
    conn.commit()
    conn.close()
    return jsonify({"message":"Bus added successfully"})

# -----------------------------
# Delete Bus
# -----------------------------
@app.route('/delete_bus/<int:bus_id>', methods=['DELETE'])
def delete_bus(bus_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM buses WHERE id=?", (bus_id,))
    conn.commit()
    conn.close()
    return jsonify({"message":"Bus deleted successfully"})

# -----------------------------
# Get Routes
# -----------------------------
@app.route('/get_routes', methods=['GET'])
def get_routes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id,start_point,end_point,stops FROM routes")
    routes = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in routes])

# -----------------------------
# Add Route
# -----------------------------
@app.route('/add_route', methods=['POST'])
def add_route():
    data = request.get_json()
    print("Received data:", data)  # debug
    start_point = data.get("start_point")
    end_point = data.get("end_point")
    stops = data.get("stops") or ""

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO routes (start_point,end_point,stops) VALUES (?,?,?)", (start_point,end_point,stops))
        conn.commit()
    except Exception as e:
        print("Error inserting route:", e)
        return jsonify({"message":"Failed to add route"}),500
    finally:
        conn.close()
    return jsonify({"message":"Route added successfully"})

# -----------------------------
# Delete Route
# -----------------------------
@app.route('/delete_route/<int:route_id>', methods=['DELETE'])
def delete_route(route_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM routes WHERE id=?", (route_id,))
    conn.commit()
    conn.close()
    return jsonify({"message":"Route deleted successfully"})
# Get stops for a route
@app.route('/get_stops/<int:route_id>', methods=['GET'])
def get_stops(route_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, stop_name FROM stops WHERE route_id=?", (route_id,))
    stops = cursor.fetchall()
    conn.close()
    return jsonify([dict(s) for s in stops])

# Add a stop
@app.route('/add_stop', methods=['POST'])
def add_stop():
    data = request.get_json()
    route_id = data.get("route_id")
    stop_name = data.get("stop_name")
    if not route_id or not stop_name:
        return jsonify({"message":"Route or stop missing"}),400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stops (route_id, stop_name) VALUES (?,?)", (route_id, stop_name))
    conn.commit()
    conn.close()
    return jsonify({"message":"Stop added successfully"})

# Delete a stop
@app.route('/delete_stop/<int:stop_id>', methods=['DELETE'])
def delete_stop(stop_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stops WHERE id=?", (stop_id,))
    conn.commit()
    conn.close()
    return jsonify({"message":"Stop deleted successfully"})

@app.route('/get_student/<int:student_id>', methods=['GET'])
def get_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id,name,email,center,address,fees FROM students WHERE id=?", (student_id,))
    student = cursor.fetchone()

    conn.close()

    if student:
        return jsonify(dict(student))
    else:
        return jsonify({"message":"Student not found"})

# -----------------------------
# Run Server (last line)
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)

