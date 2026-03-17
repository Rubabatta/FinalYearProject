import sqlite3
import hashlib
import os

# Database name
DB_NAME = os.path.join(os.path.dirname(__file__), "database.db")

# Connect to SQLite DB (create if not exists)
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# -----------------------------
# Students Table
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    center TEXT NOT NULL,
    studentID TEXT UNIQUE,
    contact TEXT,
    fees REAL
)
''')

# -----------------------------
# Admins Table
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Admin table me default admin
admin_username = "admin"
admin_password = hashlib.sha256("123".encode()).hexdigest()
cursor.execute("""
INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)
""", (admin_username, admin_password))

# -----------------------------
# Drivers Table
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    password TEXT,
    contact TEXT,
    assigned_bus_id INTEGER
)
''')

# -----------------------------
# Routes Table
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_point TEXT NOT NULL,
    end_point TEXT NOT NULL,
    stops TEXT
)
''')

# -----------------------------
# Buses Table
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS buses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_number TEXT NOT NULL,
    driver_id INTEGER,
    capacity INTEGER,
    route_id INTEGER,
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (route_id) REFERENCES routes(id)
)
''')

# -----------------------------
# Bus Locations Table
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS bus_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_id INTEGER NOT NULL,
    latitude REAL,
    longitude REAL,
    last_updated TEXT,
    FOREIGN KEY (bus_id) REFERENCES buses(id)
)
''')

# -----------------------------
# Stops Table
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER,
    stop_name TEXT,
    FOREIGN KEY(route_id) REFERENCES routes(id)
)
''')
# -----------------------------
# Announcements Table
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    date TEXT
)
''')
# Commit changes and close connection
conn.commit()
conn.close()

print("✅ Database and all tables created successfully!")