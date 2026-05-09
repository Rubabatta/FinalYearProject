from flask_cors import CORS
import sqlite3
import hashlib
import os
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(BASE_DIR, "database.db")
STATIC_FOLDER = "static"
PROFILE_FOLDER = "static/profile"

print("🚀 SERVER STARTING")
print("DB PATH:", DB_NAME)



@app.route('/test')
def test():
    return "OK WORKING"

# -----------------------------
# Database Connection
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
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
        studentID,
        center,
        contact,
        fees,
        image
        FROM students
    """)

    students = cursor.fetchall()
    conn.close()

    return jsonify([dict(s) for s in students])

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
    studentID = data.get('studentID')
    center = data.get('center')
    contact = data.get('contact')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE students
        SET name=?, email=?, studentID=?, center=?, contact=?, password=?
        WHERE id=?
    """, (name, email, studentID, center, contact, password, id))

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

@app.route('/update_bus/<int:id>', methods=['PUT'])
def update_bus(id):

    data = request.get_json()

    bus_number = data.get("bus_number")
    driver_id = data.get("driver_id")
    capacity = data.get("capacity")
    route_id = data.get("route_id")

    conn = get_db_connection()
    cursor = conn.cursor()

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

    cursor.execute("SELECT * FROM stops WHERE route_id=? ORDER BY id ASC", (route_id,))

    stops = cursor.fetchall()

    conn.close()

    return jsonify([dict(s) for s in stops])

@app.route('/add_stop', methods=['POST'])
def add_stop():
    data = request.get_json()
    route_id = data.get('route_id')
    stop_name = data.get('stop_name')

    if not route_id or not stop_name:
        return jsonify({"message":"Route and stop name are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO stops (route_id, stop_name) VALUES (?, ?)",
        (route_id, stop_name)
    )

    conn.commit()
    conn.close()

    return jsonify({"message":"Stop added successfully"})

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



@app.route('/update_location', methods=['POST'])
def update_location():

    data = request.get_json()

    bus_id = data.get('bus_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    print("📩 RECEIVED:", data)   # 👈 optional debug

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bus_locations
        (bus_id, latitude, longitude, last_updated)
        VALUES (?, ?, ?, datetime('now'))
    """, (bus_id, latitude, longitude))

    conn.commit()

    # ⭐ THIS LINE ADD HERE 👇
    print("📍 LOCATION SAVED:", bus_id, latitude, longitude)

    conn.close()

    return jsonify({"message": "Location updated"})
@app.route('/get_location/<int:bus_id>')
def get_location(bus_id):

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM bus_locations
            WHERE bus_id=?
            ORDER BY id DESC
            LIMIT 1
        """, (bus_id,))

        location = cursor.fetchone()
        conn.close()

        if location:
            return jsonify(dict(location))
        else:
            return jsonify({"message": "No location found"})

    except Exception as e:
        return jsonify({"error": str(e)})
    

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
        SELECT bl.*
        FROM bus_locations bl
        INNER JOIN (
            SELECT bus_id, MAX(id) as max_id
            FROM bus_locations
            GROUP BY bus_id
        ) latest
        ON bl.id = latest.max_id
    """)

    locations = cursor.fetchall()

    conn.close()

    return jsonify([dict(row) for row in locations])

#==================================student get loc by route================


@app.route('/get_bus_by_route/<route_number>')
def get_bus_by_route(route_number):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM buses
        WHERE route_id = ?
        LIMIT 1
    """, (route_number,))

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

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # DEBUG
        print("LOGIN ATTEMPT:", email, password)

        cursor.execute("""
            SELECT * FROM drivers WHERE email=?
        """, (email,))

        driver = cursor.fetchone()
        conn.close()

        if driver:
            db_pass = driver["password"]

            # direct compare (simple version)
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
@app.route('/add_driver', methods=['POST'])
def add_driver():
    data = request.get_json()

    print("DATA RECEIVED:", data)

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    contact = data.get('contact')
    route_number = data.get('route_number')

    if not all([name, email, password]):
        return jsonify({"message": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM drivers WHERE email=?", (email,))
        if cursor.fetchone():
            return jsonify({"message": "Driver already exists"}), 400

        cursor.execute("""
            INSERT INTO drivers (name, email, password, contact, route_number)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, password, contact, route_number))

        conn.commit()
        return jsonify({"message": "Driver added successfully"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"message": "Server error"}), 500

    finally:
        conn.close()


@app.route('/get_drivers', methods=['GET'])
def get_drivers():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM drivers")
    drivers = cursor.fetchall()

    conn.close()

    return jsonify([dict(d) for d in drivers])


@app.route('/update_driver/<int:id>', methods=['PUT'])
def update_driver(id):
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    contact = data.get('contact')
    route_number = data.get('route_number')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE drivers
        SET name=?, email=?, contact=?, route_number=?
        WHERE id=?
    """, (name, email, contact, route_number, id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Driver updated successfully"})


@app.route('/delete_driver/<int:id>', methods=['DELETE'])
def delete_driver(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM drivers WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"message": "Driver deleted successfully"})


    
# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)