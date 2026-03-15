from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib

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
    studentID = data.get('studentID')
    contact = data.get('contact')
    fees = data.get('fees')

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

    # Hash the incoming password before comparing
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM admins WHERE username=? AND password=?",
        (username, password_hash)
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
# ROUTES CRUD
# -----------------------------

# Get Routes
@app.route('/get_routes', methods=['GET'])
def get_routes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM routes")

    routes = cursor.fetchall()

    conn.close()

    return jsonify([dict(r) for r in routes])


# Add Route
@app.route('/add_route', methods=['POST'])
def add_route():

    data = request.get_json()

    start = data.get("start_point")
    end = data.get("end_point")
    stops = data.get("stops") or ""   # Ensure stops is not None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO routes (start_point,end_point,stops)
        VALUES (?,?,?)
    """,(start,end,stops))

    conn.commit()
    conn.close()

    return jsonify({"message":"Route added successfully"})


# Update Route
@app.route('/update_route/<int:id>', methods=['PUT'])
def update_route(id):

    data = request.get_json()

    start = data.get("start_point")
    end = data.get("end_point")
    stops = data.get("stops") or ""  # Fix to allow updating stops

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE routes
        SET start_point=?, end_point=?, stops=?
        WHERE id=?
    """,(start,end,stops,id))

    conn.commit()
    conn.close()

    return jsonify({"message":"Route updated successfully"})


# Delete Route
@app.route('/delete_route/<int:id>', methods=['DELETE'])
def delete_route(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM routes WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"message":"Route deleted successfully"})


# -----------------------------
# BUSES CRUD
# -----------------------------

# Get Buses
@app.route('/get_buses', methods=['GET'])
def get_buses():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT buses.*, routes.start_point, routes.end_point
        FROM buses
        LEFT JOIN routes
        ON buses.route_id = routes.id
    """)

    buses = cursor.fetchall()

    conn.close()

    return jsonify([dict(b) for b in buses])


# Add Bus
@app.route('/add_bus', methods=['POST'])
def add_bus():

    data = request.get_json()

    bus_number = data.get("bus_number")
    driver_id = data.get("driver_id")
    capacity = data.get("capacity")
    route_id = data.get("route_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM buses WHERE bus_number=?", (bus_number,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return jsonify({"message":"Bus number already exists"}),400

    cursor.execute("""
        INSERT INTO buses (bus_number,driver_id,capacity,route_id)
        VALUES (?,?,?,?)
    """,(bus_number,driver_id,capacity,route_id))

    conn.commit()
    conn.close()

    return jsonify({"message":"Bus added successfully"})

# Update Bus
@app.route('/update_bus/<int:id>', methods=['PUT'])
def update_bus(id):

    data = request.get_json()

    bus_number = data.get("bus_number")
    driver_id = data.get("driver_id")
    capacity = data.get("capacity")
    route_id = data.get("route_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check unique bus_number except current bus
    cursor.execute("SELECT * FROM buses WHERE bus_number=? AND id!=?", (bus_number,id))
    if cursor.fetchone():
        conn.close()
        return jsonify({"message":"Bus number already exists"}),400

    cursor.execute("""
        UPDATE buses
        SET bus_number=?,driver_id=?,capacity=?,route_id=?
        WHERE id=?
    """,(bus_number,driver_id,capacity,route_id,id))

    conn.commit()
    conn.close()

    return jsonify({"message":"Bus updated successfully"})


# Delete Bus
@app.route('/delete_bus/<int:id>', methods=['DELETE'])
def delete_bus(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM buses WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"message":"Bus deleted successfully"})


# -----------------------------
# Get Stops for a Route
# -----------------------------
@app.route('/get_stops/<int:route_id>', methods=['GET'])
def get_stops(route_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stops WHERE route_id=?", (route_id,))
    stops = cursor.fetchall()
    conn.close()
    return jsonify([dict(s) for s in stops])

# -----------------------------
# Add Stop
# -----------------------------
@app.route('/add_stop', methods=['POST'])
def add_stop():
    data = request.get_json()
    route_id = data.get('route_id')
    stop_name = data.get('stop_name')

    if not route_id or not stop_name:
        return jsonify({"message":"Route and stop name are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stops (route_id, stop_name) VALUES (?, ?)", (route_id, stop_name))
    conn.commit()
    conn.close()
    return jsonify({"message":"Stop added successfully"})

# -----------------------------
# Update Stop
# -----------------------------
@app.route('/update_stop/<int:id>', methods=['PUT'])
def update_stop(id):
    data = request.get_json()
    stop_name = data.get('stop_name')
    if not stop_name:
        return jsonify({"message":"Stop name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE stops SET stop_name=? WHERE id=?", (stop_name, id))
    conn.commit()
    conn.close()
    return jsonify({"message":"Stop updated successfully"})

# -----------------------------
# Delete Stop
# -----------------------------
@app.route('/delete_stop/<int:id>', methods=['DELETE'])
def delete_stop(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stops WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message":"Stop deleted successfully"})

# -----------------------------
# Run Server
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)