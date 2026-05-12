from flask_cors import CORS
import sqlite3
import hashlib
import os
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timedelta

if os.path.exists("/data"):
    DB_NAME = "/data/database.db"
else:
    DB_NAME = os.path.join(os.path.dirname(__file__), "database.db")

# -----------------------------
# Database Connection
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        center TEXT,
        studentID TEXT UNIQUE,
        contact TEXT,
        fees REAL,
        image TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute("INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)", (
        "admin",
        hashlib.sha256("123".encode()).hexdigest()
    ))

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_point TEXT NOT NULL,
        end_point TEXT NOT NULL,
        stops TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_number TEXT UNIQUE NOT NULL,
        driver_id INTEGER,
        capacity INTEGER,
        route_id INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bus_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_id INTEGER NOT NULL,
        latitude REAL,
        longitude REAL,
        last_updated TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER,
        stop_name TEXT,
        latitude REAL,
        longitude REAL,
        stop_order INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        date TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        password TEXT,
        contact TEXT,
        bus_id INTEGER,
        route_id INTEGER
    )
    ''')

    for statement in [
        "ALTER TABLE students ADD COLUMN image TEXT",
        "ALTER TABLE students ADD COLUMN route_id INTEGER",
        "ALTER TABLE students ADD COLUMN stop_id INTEGER",
        "ALTER TABLE stops ADD COLUMN latitude REAL",
        "ALTER TABLE stops ADD COLUMN longitude REAL",
        "ALTER TABLE drivers ADD COLUMN bus_id INTEGER",
        "ALTER TABLE drivers ADD COLUMN route_id INTEGER",
    ]:
        try:
            cursor.execute(statement)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def normalize_route_ids():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM routes ORDER BY id ASC")
    rows = cursor.fetchall()

    mapping = {}
    next_id = 1
    for row in rows:
        old_id = row["id"]
        if old_id != next_id:
            mapping[old_id] = next_id
        next_id += 1

    if not mapping:
        conn.close()
        return

    for old_id, new_id in mapping.items():
        cursor.execute("UPDATE routes SET id = ? WHERE id = ?", (-new_id, old_id))

    for table in ["buses", "stops", "drivers"]:
        for old_id, new_id in mapping.items():
            cursor.execute(f"UPDATE {table} SET route_id = ? WHERE route_id = ?", (-new_id, old_id))

    for table in ["buses", "stops", "drivers"]:
        for old_id, new_id in mapping.items():
            cursor.execute(f"UPDATE {table} SET route_id = ? WHERE route_id = ?", (new_id, -new_id))

    for old_id, new_id in mapping.items():
        cursor.execute("UPDATE routes SET id = ? WHERE id = ?", (new_id, -new_id))

    cursor.execute("SELECT MAX(id) as max_id FROM routes")
    max_id = cursor.fetchone()["max_id"] or 0
    try:
        cursor.execute("INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('routes', ?)", (max_id,))
    except sqlite3.OperationalError:
        # Skip if sqlite_sequence does not exist yet
        pass

    conn.commit()
    conn.close()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

STATIC_FOLDER = "static"
PROFILE_FOLDER = "static/profile"

print("🚀 SERVER STARTING")
print("DB PATH:", DB_NAME)

# -----------------------------
# Auto-populate DB if empty (for Railway)
# -----------------------------
def auto_populate_if_empty():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if students table has data
    try:
        cursor.execute("SELECT COUNT(*) FROM students")
    except sqlite3.OperationalError:
        conn.close()
        initialize_database()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")

    if cursor.fetchone()[0] == 0:
        print("DB is empty, populating with sample data...")

        # Add latitude and longitude to stops if not exists
        try:
            cursor.execute("ALTER TABLE stops ADD COLUMN latitude REAL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE stops ADD COLUMN longitude REAL")
        except:
            pass

        # Add route_id column to drivers if not exists
        try:
            cursor.execute("ALTER TABLE drivers ADD COLUMN route_id INTEGER")
        except:
            pass

        # Sample Routes
        routes_data = [
            ("Campus Main Gate", "City Center", "Gate 1, Library, Cafeteria, City Stop 1, City Stop 2, City Center Plaza"),
            ("Hostel Block A", "Airport", "Hostel A, Academic Block, Sports Complex, Highway Entry, Airport Terminal 1, Airport Terminal 2"),
            ("Library", "Mall", "Library Entrance, Science Block, Engineering Block, Mall Parking, Mall Entrance, Food Court")
        ]
        for start, end, stops in routes_data:
            cursor.execute("INSERT OR IGNORE INTO routes (start_point, end_point, stops) VALUES (?, ?, ?)", (start, end, stops))

        # Sample Buses
        buses_data = [
            ("BUS-001", 1, 50),
            ("BUS-002", 2, 45),
            ("BUS-003", 3, 40),
            ("BUS-004", 1, 55),
            ("BUS-005", 2, 35),
        ]
        for bus_num, route_id, capacity in buses_data:
            cursor.execute("INSERT OR IGNORE INTO buses (bus_number, route_id, capacity) VALUES (?, ?, ?)", (bus_num, route_id, capacity))

        # Sample Drivers
        drivers_data = [
            ("Ahmed Khan", "ahmed@example.com", "123", "03001234567", 1),
            ("Sara Ali", "sara@example.com", "123", "03009876543", 2),
        ]
        for name, email, password, contact, bus_id in drivers_data:
            cursor.execute("INSERT OR IGNORE INTO drivers (name, email, password, contact, bus_id) VALUES (?, ?, ?, ?, ?)", (name, email, password, contact, bus_id))

        # Update buses driver_id
        cursor.execute("""
        UPDATE buses 
        SET driver_id = (
            SELECT d.id 
            FROM drivers d 
            WHERE d.bus_id = buses.id
        )
        WHERE EXISTS (
            SELECT 1 
            FROM drivers d 
            WHERE d.bus_id = buses.id
        )
        """)

        # Sample Stops
        stops_data = [
            (1, "Campus Main Gate", 31.5204, 74.3587, 1),
            (1, "Library", 31.5220, 74.3600, 2),
            (1, "Cafeteria", 31.5235, 74.3615, 3),
            (1, "City Stop 1", 31.5250, 74.3630, 4),
            (1, "City Stop 2", 31.5265, 74.3645, 5),
            (1, "City Center Plaza", 31.5280, 74.3660, 6),
            (2, "Hostel Block A", 31.5300, 74.3680, 1),
            (2, "Academic Block", 31.5315, 74.3695, 2),
            (2, "Sports Complex", 31.5330, 74.3710, 3),
            (2, "Highway Entry", 31.5345, 74.3725, 4),
            (2, "Airport Terminal 1", 31.5360, 74.3740, 5),
            (2, "Airport Terminal 2", 31.5375, 74.3755, 6),
            (3, "Library Entrance", 31.5390, 74.3770, 1),
            (3, "Science Block", 31.5405, 74.3785, 2),
            (3, "Engineering Block", 31.5420, 74.3800, 3),
            (3, "Mall Parking", 31.5435, 74.3815, 4),
            (3, "Mall Entrance", 31.5450, 74.3830, 5),
            (3, "Food Court", 31.5465, 74.3845, 6)
        ]
        for route_id, stop_name, lat, lng, order in stops_data:
            cursor.execute("INSERT OR IGNORE INTO stops (route_id, stop_name, latitude, longitude, stop_order) VALUES (?, ?, ?, ?, ?)", (route_id, stop_name, lat, lng, order))

        # Sample Students
        students_data = [
            ("Ali Ahmed", "ali@example.com", "123", "Main Campus", "STU001", "03001234567", 5000.0),
            ("Fatima Khan", "fatima@example.com", "123", "City Branch", "STU002", "03009876543", 4500.0),
            ("Omar Hassan", "omar@example.com", "123", "Main Campus", "STU003", "03005556677", 5000.0),
            ("Ayesha Malik", "ayesha@example.com", "123", "City Branch", "STU004", "03004443322", 4500.0),
            ("Hassan Raza", "hassan@example.com", "123", "Main Campus", "STU005", "03001112233", 5000.0)
        ]
        for name, email, password, center, studentID, contact, fees in students_data:
            cursor.execute("INSERT OR IGNORE INTO students (name, email, password, center, studentID, contact, fees) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, email, password, center, studentID, contact, fees))

        # Sample Announcements
        announcements_data = [
            ("Welcome to New Semester", "All students are welcome to the new semester. Please check your schedules.", "2024-01-01"),
            ("Bus Route Changes", "Due to construction, Route 1 has been modified. Check the app for updates.", "2024-01-15"),
            ("Fee Payment Reminder", "Last date for fee payment is approaching. Pay online to avoid late fees.", "2024-02-01")
        ]
        for title, message, date in announcements_data:
            cursor.execute("INSERT OR IGNORE INTO announcements (title, message, date) VALUES (?, ?, ?)", (title, message, date))

        conn.commit()
        print("Sample data populated ✅")
    else:
        print("DB has data, skipping population")

    conn.close()

initialize_database()
normalize_route_ids()
auto_populate_if_empty()

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
    contact = data.get('contact')
    fees = data.get('fees')
    route_id = data.get('route_id')
    stop_id = data.get('stop_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE email=?", (email,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return jsonify({"message":"Email already exists"}),400

    try:
        cursor.execute("""
            INSERT INTO students (name,email,password,contact,fees,route_id,stop_id)
            VALUES (?,?,?,?,?,?,?)
        """, (name,email,password,contact,fees,route_id,stop_id))

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

    return jsonify({"message":"Invalid username or password"}),401


# =============================
# ⭐ SINGLE LOGIN (NEW FIX ADDED HERE)
# =============================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    # -------------------------
    # 1️⃣ Check Student Login
    # -------------------------
    cursor.execute(
        "SELECT * FROM students WHERE email=? AND password=?",
        (email, password)
    )
    student = cursor.fetchone()

    if student:
        conn.close()
        return jsonify({
            "role": "student",
            "user": dict(student)
        })

    # -------------------------
    # 2️⃣ Check Admin Login
    # -------------------------
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute(
        "SELECT * FROM admins WHERE username=? AND password=?",
        (email, password_hash)
    )
    admin = cursor.fetchone()

    conn.close()

    if admin:
        return jsonify({
            "role": "admin",
            "user": dict(admin)
        })

    return jsonify({"message": "Invalid login"}), 401

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
        contact,
        fees,
        image,
        route_id,
        stop_id
        FROM students
    """)

    students = cursor.fetchall()
    conn.close()

    return jsonify([dict(s) for s in students])

# -----------------------------
# Get single student (for edit)
# -----------------------------
@app.route('/get_student/<int:id>', methods=['GET'])
def get_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cursor.fetchone()
    conn.close()

    if student:
        return jsonify(dict(student))
    else:
        return jsonify({"message":"Student not found"}), 404

# -----------------------------
# Update Student
# -----------------------------
@app.route('/update_student/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    contact = data.get('contact')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    if password:
        cursor.execute("""
            UPDATE students
            SET name=?, email=?, contact=?, password=?
            WHERE id=?
        """, (name, email, contact, password, id))
    else:
        cursor.execute("""
            UPDATE students
            SET name=?, email=?, contact=?
            WHERE id=?
        """, (name, email, contact, id))

    conn.commit()
    conn.close()

    return jsonify({"message":"Student updated successfully"})

# -----------------------------
# Delete Student
# -----------------------------
@app.route('/delete_student/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message":"Student deleted successfully"})

# -----------------------------
# Routes CRUD
# -----------------------------
@app.route('/get_routes', methods=['GET'])
def get_routes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM routes")

    routes = cursor.fetchall()

    conn.close()

    return jsonify([dict(r) for r in routes])

@app.route('/add_route', methods=['POST'])
def add_route():

    data = request.get_json()

    start = data.get("start_point")
    end = data.get("end_point")
    stops = data.get("stops") or ""

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO routes (start_point,end_point,stops)
        VALUES (?,?,?)
    """,(start,end,stops))

    conn.commit()
    conn.close()

    normalize_route_ids()

    return jsonify({"message":"Route added successfully"})

@app.route('/update_route/<int:id>', methods=['PUT'])
def update_route(id):

    data = request.get_json()

    start = data.get("start_point")
    end = data.get("end_point")
    stops = data.get("stops") or ""

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

@app.route('/delete_route/<int:id>', methods=['DELETE'])
def delete_route(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM routes WHERE id=?", (id,))

    conn.commit()
    conn.close()

    normalize_route_ids()

    return jsonify({"message":"Route deleted successfully"})

# -----------------------------
# Buses CRUD
# -----------------------------
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

@app.route('/get_bus/<int:id>', methods=['GET'])
def get_bus(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM buses WHERE id = ?", (id,))
    bus = cursor.fetchone()
    conn.close()

    if bus:
        return jsonify(dict(bus))
    return jsonify({"message": "Bus not found"}), 404

@app.route('/add_bus', methods=['POST'])
def add_bus():

    data = request.get_json()

    bus_number = data.get("bus_number")
    route_id = data.get("route_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM buses WHERE bus_number=?", (bus_number,))
        if cursor.fetchone():
            return jsonify({"message":"Bus number already exists"}),400

        cursor.execute("""
            INSERT INTO buses (bus_number, route_id)
            VALUES (?, ?)
        """,(bus_number, route_id))

        conn.commit()
        return jsonify({"message":"Bus added successfully"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"message":"Server error"}),500

    finally:
        conn.close()

@app.route('/update_bus/<int:id>', methods=['PUT'])
def update_bus(id):

    data = request.get_json()

    bus_number = data.get("bus_number")
    driver_id = data.get("driver_id")
    capacity = data.get("capacity")
    route_id = data.get("route_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM buses WHERE id = ?", (id,))
    existing_bus = cursor.fetchone()
    if not existing_bus:
        conn.close()
        return jsonify({"message": "Bus not found"}), 404

    cursor.execute("SELECT * FROM buses WHERE bus_number=? AND id!=?", (bus_number, id))
    if cursor.fetchone():
        conn.close()
        return jsonify({"message":"Bus number already exists"}),400

    driver_id = driver_id if driver_id is not None else existing_bus["driver_id"]
    capacity = capacity if capacity is not None else existing_bus["capacity"]
    route_id = route_id if route_id is not None else existing_bus["route_id"]

    cursor.execute("""
        UPDATE buses
        SET bus_number=?, driver_id=?, capacity=?, route_id=?
        WHERE id=?
    """, (bus_number, driver_id, capacity, route_id, id))

    conn.commit()
    conn.close()

    return jsonify({"message":"Bus updated successfully"})

@app.route('/delete_bus/<int:id>', methods=['DELETE'])
def delete_bus(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM buses WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"message":"Bus deleted successfully"})

# -----------------------------
# Stops CRUD
# -----------------------------
@app.route('/get_stops/<int:route_id>', methods=['GET'])
def get_stops(route_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM stops WHERE route_id=? ORDER BY stop_order ASC, id ASC", (route_id,))

    stops = cursor.fetchall()

    conn.close()

    return jsonify([dict(s) for s in stops])

@app.route("/add_stop", methods=["POST"])
def add_stop():

    data = request.json

    route_id = data.get("route_id")
    stop_name = data.get("stop_name")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 👉 get max order
        cursor.execute("SELECT MAX(stop_order) FROM stops WHERE route_id=?", (route_id,))
        max_order = cursor.fetchone()[0]
        if max_order is None:
            max_order = 0

        cursor.execute("""
        INSERT INTO stops
        (route_id, stop_name, latitude, longitude, stop_order)
        VALUES (?, ?, ?, ?, ?)
        """, (route_id, stop_name, latitude, longitude, max_order+1))

        conn.commit()
    finally:
        conn.close()

    return jsonify({"message":"Stop added successfully"})

@app.route('/update_stop/<int:id>', methods=['PUT'])
def update_stop(id):

    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE stops
            SET stop_name=?, latitude=?, longitude=?
            WHERE id=?
        """, (
            data['stop_name'],
            data['latitude'],
            data['longitude'],
            id
        ))

        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Stop updated"})
@app.route('/delete_stop/<int:id>', methods=['DELETE'])
def delete_stop(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT route_id FROM stops WHERE id=?", (id,))
    row = cursor.fetchone()

    cursor.execute("DELETE FROM stops WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"message":"Stop deleted successfully"})

# -----------------------------
# Announcements CRUD (Student & Admin)
# -----------------------------
@app.route('/add-announcement', methods=['POST'])
def add_announcement():
    data = request.get_json()
    title = data.get('title')
    message = data.get('message')
    date = data.get('date')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO announcements (title,message,date) VALUES (?,?,?)",
                   (title,message,date))
    conn.commit()
    conn.close()
    return jsonify({"message":"Added successfully"})

@app.route('/get-announcements', methods=['GET'])
def get_announcements():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM announcements ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "title": row["title"],
            "message": row["message"],
            "date": row["date"]
        })
    return jsonify(result)

@app.route('/delete-announcement/<int:id>', methods=['DELETE'])
def delete_announcement(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM announcements WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message":"Deleted successfully"})

@app.route('/update-announcement/<int:id>', methods=['PUT'])
def update_announcement(id):
    data = request.get_json()
    title = data.get('title')
    message = data.get('message')
    date = data.get('date')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE announcements SET title=?, message=?, date=? WHERE id=?",
                   (title,message,date,id))
    conn.commit()
    conn.close()
    return jsonify({"message":"Updated successfully"})  


@app.route('/change_admin_password', methods=['POST'])
def change_admin_password():
    data = request.get_json()

    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    old_hash = hashlib.sha256(old_password.encode()).hexdigest()
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    # check admin exists
    cursor.execute(
        "SELECT * FROM admins WHERE username=? AND password=?",
        (username, old_hash)
    )
    admin = cursor.fetchone()

    if not admin:
        conn.close()
        return jsonify({"message": "Old password incorrect"}), 401

    # update password
    cursor.execute(
        "UPDATE admins SET password=? WHERE username=?",
        (new_hash, username)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Password changed successfully"})

@app.route("/upload_profile_img", methods=["POST"])
def upload_profile_img():

    file = request.files["image"]
    student_id = request.form["student_id"]

    os.makedirs(PROFILE_FOLDER, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    if ext == "":
        ext = ".jpg"

    filename = f"{student_id}{ext}"
    path = os.path.join(PROFILE_FOLDER, filename)

    file.save(path)

    image_url = f"/static/profile/{filename}"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE students SET image=? WHERE id=?",
        (image_url, student_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "image_url": image_url
    })
   
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

#============location traking root=============================


@app.route('/get_latest_location/<int:bus_id>', methods=['GET'])
def get_latest_location(bus_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM bus_locations
        WHERE bus_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (bus_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify(dict(row))
    else:
        return jsonify({"message": "No location found"}), 404


@app.route('/update_location', methods=['POST'])
def update_location():

    data = request.get_json()

    bus_id = data.get('bus_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bus_locations
        (bus_id, latitude, longitude, last_updated)
        VALUES (?, ?, ?, ?)
    """, (bus_id, latitude, longitude, now))

    conn.commit()
    conn.close()

    return jsonify({"message": "Location updated"})
    #.......................
    #  All Location
    #========================


    # =========================
# GET ALL BUSES LOCATION
# =========================
@app.route('/get_all_locations', methods=['GET'])
def get_all_locations():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        bl.bus_id,
        bl.latitude,
        bl.longitude,
        bl.last_updated,
        b.bus_number,
        b.route_id
    FROM bus_locations bl
    LEFT JOIN buses b ON bl.bus_id = b.id
    ORDER BY bl.id DESC
""")
    rows = cursor.fetchall()
    conn.close()

    result = []
    seen = set()
    now = datetime.now()

    def parse_time(t):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(t, fmt)
            except:
                pass
        return None

    for row in rows:

        bus_id = row["bus_id"]

        if bus_id in seen:
            continue

        seen.add(bus_id)
        result.append(dict(row))

    return jsonify(result)
# =========================
# GET SINGLE BUS LOCATION
# =========================
@app.route('/get_location/<int:bus_id>', methods=['GET'])
def get_location(bus_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM bus_locations
        WHERE bus_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (bus_id,))

    row = cursor.fetchone()

    conn.close()

    if row:
        return jsonify(dict(row))
    else:
        return jsonify({
            "message": "No location found"
        }), 404
#==================================student get loc by route================


@app.route('/get_bus_by_route/<int:route_id>')
def get_bus_by_route(route_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM buses
        WHERE route_id = ?
        LIMIT 1
    """, (route_id,))

    bus = cursor.fetchone()
    conn.close()

    if bus:
        return jsonify(dict(bus))
    else:
        return jsonify({"message": "No bus found for this route"})
# -----------------------------
# FRONTEND ROUTE (ADD THIS)
# -----------------------------
#@app.route('/frontend/<path:filename>')
#def frontend(filename):
    #return send_from_directory('../frontend', filename)

#@app.route('/mobile.html')
#def mobile():
    #return send_from_directory('../frontend', 'mobile.html')

#//////////////////////
#  Driver Login
#//////////////////////

@app.route('/driver_login', methods=['POST'])
def driver_login():
    try:
        data = request.get_json()

        identifier = data.get('email') or data.get('name') or data.get('identifier')
        password = data.get('password')

        if not identifier or not password:
            return jsonify({"message": "Email/name and password required"}), 400

        identifier = identifier.strip().lower()

        conn = get_db_connection()
        cursor = conn.cursor()

        print("LOGIN ATTEMPT:", identifier, password)

        # ✅ FIX: email OR name both check
        cursor.execute("""
            SELECT 
    drivers.*,
    buses.bus_number
FROM drivers
LEFT JOIN buses ON drivers.bus_id = buses.id
WHERE LOWER(drivers.email)=? OR LOWER(drivers.name)=?
        """, (identifier, identifier))

        driver = cursor.fetchone()
        conn.close()

        if driver:
            db_pass = driver["password"]

            if db_pass == password:
                return jsonify({
                    "message": "Login successful",
                    "driver": dict(driver)
                }), 200
            else:
                return jsonify({"message": "Wrong password"}), 401

        return jsonify({"message": "Driver not found"}), 404

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"message": str(e)}), 500
#......................
#Add Driver
#......................
# =========================
# DRIVER MODULE (CLEAN)
# =========================

@app.route('/add_driver', methods=['POST'])
def add_driver():

    try:

        data = request.get_json()

        print("DATA RECEIVED:", data)

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        contact = data.get('contact')

        bus_id = data.get('bus_id')

        if bus_id == "" or bus_id is None:
            bus_id = None

        conn = get_db_connection()
        cursor = conn.cursor()

        route_id = None
        if bus_id is not None:
            cursor.execute("SELECT route_id FROM buses WHERE id=?", (bus_id,))
            row = cursor.fetchone()
            if row:
                route_id = row["route_id"] if isinstance(row, dict) else row[0]

        # Check if drivers table supports route_id
        cursor.execute("PRAGMA table_info(drivers)")
        driver_columns = [row[1] for row in cursor.fetchall()]
        has_route_id = 'route_id' in driver_columns

        try:
            if has_route_id:
                cursor.execute("""
                    INSERT INTO drivers
                    (name, email, password, contact, bus_id, route_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    email,
                    password,
                    contact,
                    bus_id,
                    route_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO drivers
                    (name, email, password, contact, bus_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    name,
                    email,
                    password,
                    contact,
                    bus_id
                ))

            conn.commit()
        finally:
            conn.close()

        return jsonify({
            "message": "Driver added successfully"
        })

    except Exception as e:

        print("ADD DRIVER ERROR:", str(e))

        return jsonify({
            "message": str(e)
        }), 500
# GET DRIVERS
@app.route('/get_drivers', methods=['GET'])
def get_drivers():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(drivers)")
    driver_columns = [row[1] for row in cursor.fetchall()]
    has_route_id = 'route_id' in driver_columns

    if has_route_id:
        cursor.execute("""
            SELECT 
                d.id,
                d.name,
                d.email,
                d.contact,
                d.bus_id,
                d.route_id,
                b.bus_number,
                b.route_id as bus_route_id,
                routes.start_point,
                routes.end_point,
                CASE
                    WHEN routes.start_point IS NOT NULL THEN routes.start_point || ' - ' || routes.end_point
                    ELSE NULL
                END AS route_name
            FROM drivers d
            LEFT JOIN buses b ON d.bus_id = b.id
            LEFT JOIN routes ON COALESCE(d.route_id, b.route_id) = routes.id
        """)
    else:
        cursor.execute("""
            SELECT 
                d.id,
                d.name,
                d.email,
                d.contact,
                d.bus_id,
                b.bus_number,
                b.route_id as bus_route_id,
                routes.start_point,
                routes.end_point,
                CASE
                    WHEN routes.start_point IS NOT NULL THEN routes.start_point || ' - ' || routes.end_point
                    ELSE NULL
                END AS route_name
            FROM drivers d
            LEFT JOIN buses b ON d.bus_id = b.id
            LEFT JOIN routes ON b.route_id = routes.id
        """)

    drivers = cursor.fetchall()
    conn.close()

    return jsonify([dict(d) for d in drivers])

# UPDATE DRIVER
@app.route('/update_driver/<int:id>', methods=['PUT'])
def update_driver(id):
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    contact = data.get('contact')
    bus_id = data.get('bus_id')

    if bus_id == "" or bus_id is None:
        bus_id = None

    conn = get_db_connection()
    cursor = conn.cursor()

    route_id = None
    if bus_id is not None:
        cursor.execute("SELECT route_id FROM buses WHERE id=?", (bus_id,))
        row = cursor.fetchone()
        if row:
            route_id = row["route_id"] if isinstance(row, dict) else row[0]

    # Check if drivers table supports route_id
    cursor.execute("PRAGMA table_info(drivers)")
    driver_columns = [row[1] for row in cursor.fetchall()]
    has_route_id = 'route_id' in driver_columns

    if has_route_id:
        cursor.execute("""
            UPDATE drivers
            SET name=?, email=?, contact=?, bus_id=?, route_id=?
            WHERE id=?
        """, (name, email, contact, bus_id, route_id, id))
    else:
        cursor.execute("""
            UPDATE drivers
            SET name=?, email=?, contact=?, bus_id=?
            WHERE id=?
        """, (name, email, contact, bus_id, id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Driver updated successfully"})


# DELETE DRIVER
@app.route('/delete_driver/<int:id>', methods=['DELETE'])
def delete_driver(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM drivers WHERE id=?", (id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"message":"Driver not found"}),404

    cursor.execute("DELETE FROM drivers WHERE id=?", (id,))
    conn.commit()

    conn.close()

    return jsonify({"message":"Driver deleted successfully"})


    # =========================
# ADD bus_id COLUMN
# =========================

try:

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    ALTER TABLE drivers
    ADD COLUMN bus_id INTEGER
    """)
    conn.commit()
    print("bus_id column added ✅")

    try:
        cursor.execute("""
        ALTER TABLE drivers
        ADD COLUMN route_id INTEGER
        """)
        conn.commit()
        print("route_id column added ✅")
    except Exception as e:
        print("route_id already exists OR error:", e)

    conn.close()

except Exception as e:
    print("bus_id already exists OR error:", e)

    
    
@app.route('/populate_db', methods=['POST'])
def populate_db():
    try:
        # Run the create-db.py logic here
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add latitude and longitude to stops if not exists
        try:
            cursor.execute("ALTER TABLE stops ADD COLUMN latitude REAL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE stops ADD COLUMN longitude REAL")
        except:
            pass

        # Add route_id column to drivers if not exists
        try:
            cursor.execute("ALTER TABLE drivers ADD COLUMN route_id INTEGER")
        except:
            pass

        # Sample Routes
        routes_data = [
            ("Campus Main Gate", "City Center", "Gate 1, Library, Cafeteria, City Stop 1, City Stop 2, City Center Plaza"),
            ("Hostel Block A", "Airport", "Hostel A, Academic Block, Sports Complex, Highway Entry, Airport Terminal 1, Airport Terminal 2"),
            ("Library", "Mall", "Library Entrance, Science Block, Engineering Block, Mall Parking, Mall Entrance, Food Court")
        ]
        for start, end, stops in routes_data:
            cursor.execute("INSERT OR IGNORE INTO routes (start_point, end_point, stops) VALUES (?, ?, ?)", (start, end, stops))

        # Sample Buses
        buses_data = [
            ("BUS-001", 1, 50),
            ("BUS-002", 2, 45),
            ("BUS-003", 3, 40),
            ("BUS-004", 1, 55),
            ("BUS-005", 2, 35),
        ]
        for bus_num, route_id, capacity in buses_data:
            cursor.execute("INSERT OR IGNORE INTO buses (bus_number, route_id, capacity) VALUES (?, ?, ?)", (bus_num, route_id, capacity))

        # Sample Drivers
        drivers_data = [
            ("Ahmed Khan", "ahmed@example.com", "123", "03001234567", 1),
            ("Sara Ali", "sara@example.com", "123", "03009876543", 2),
        ]
        for name, email, password, contact, bus_id in drivers_data:
            cursor.execute("INSERT OR IGNORE INTO drivers (name, email, password, contact, bus_id) VALUES (?, ?, ?, ?, ?)", (name, email, password, contact, bus_id))

        # Update buses driver_id
        cursor.execute("""
        UPDATE buses 
        SET driver_id = (
            SELECT d.id 
            FROM drivers d 
            WHERE d.bus_id = buses.id
        )
        WHERE EXISTS (
            SELECT 1 
            FROM drivers d 
            WHERE d.bus_id = buses.id
        )
        """)

        # Sample Stops
        stops_data = [
            (1, "Campus Main Gate", 31.5204, 74.3587, 1),
            (1, "Library", 31.5220, 74.3600, 2),
            (1, "Cafeteria", 31.5235, 74.3615, 3),
            (1, "City Stop 1", 31.5250, 74.3630, 4),
            (1, "City Stop 2", 31.5265, 74.3645, 5),
            (1, "City Center Plaza", 31.5280, 74.3660, 6),
            (2, "Hostel Block A", 31.5300, 74.3680, 1),
            (2, "Academic Block", 31.5315, 74.3695, 2),
            (2, "Sports Complex", 31.5330, 74.3710, 3),
            (2, "Highway Entry", 31.5345, 74.3725, 4),
            (2, "Airport Terminal 1", 31.5360, 74.3740, 5),
            (2, "Airport Terminal 2", 31.5375, 74.3755, 6),
            (3, "Library Entrance", 31.5390, 74.3770, 1),
            (3, "Science Block", 31.5405, 74.3785, 2),
            (3, "Engineering Block", 31.5420, 74.3800, 3),
            (3, "Mall Parking", 31.5435, 74.3815, 4),
            (3, "Mall Entrance", 31.5450, 74.3830, 5),
            (3, "Food Court", 31.5465, 74.3845, 6)
        ]
        for route_id, stop_name, lat, lng, order in stops_data:
            cursor.execute("INSERT OR IGNORE INTO stops (route_id, stop_name, latitude, longitude, stop_order) VALUES (?, ?, ?, ?, ?)", (route_id, stop_name, lat, lng, order))

        # Sample Students
        students_data = [
            ("Ali Ahmed", "ali@example.com", "123", "Main Campus", "STU001", "03001234567", 5000.0),
            ("Fatima Khan", "fatima@example.com", "123", "City Branch", "STU002", "03009876543", 4500.0),
            ("Omar Hassan", "omar@example.com", "123", "Main Campus", "STU003", "03005556677", 5000.0),
            ("Ayesha Malik", "ayesha@example.com", "123", "City Branch", "STU004", "03004443322", 4500.0),
            ("Hassan Raza", "hassan@example.com", "123", "Main Campus", "STU005", "03001112233", 5000.0)
        ]
        for name, email, password, center, studentID, contact, fees in students_data:
            cursor.execute("INSERT OR IGNORE INTO students (name, email, password, center, studentID, contact, fees) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, email, password, center, studentID, contact, fees))

        # Sample Announcements
        announcements_data = [
            ("Welcome to New Semester", "All students are welcome to the new semester. Please check your schedules.", "2024-01-01"),
            ("Bus Route Changes", "Due to construction, Route 1 has been modified. Check the app for updates.", "2024-01-15"),
            ("Fee Payment Reminder", "Last date for fee payment is approaching. Pay online to avoid late fees.", "2024-02-01")
        ]
        for title, message, date in announcements_data:
            cursor.execute("INSERT OR IGNORE INTO announcements (title, message, date) VALUES (?, ?, ?)", (title, message, date))

        conn.commit()
        conn.close()

        return jsonify({"message": "Database populated successfully"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)