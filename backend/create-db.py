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

# Default admin
admin_username = "admin"
admin_password = hashlib.sha256("123".encode()).hexdigest()

cursor.execute("""
INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)
""", (admin_username, admin_password))

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
    bus_number TEXT UNIQUE NOT NULL,
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
# Stops Table (FIXED)
# -----------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER,
    stop_name TEXT,
    stop_order INTEGER,
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
    bus_id INTEGER,
    FOREIGN KEY (bus_id) REFERENCES buses(id)
)
''')
# -----------------------------
# Add image column (ONLY ONCE)
# -----------------------------
cursor.execute("PRAGMA table_info(students)")
columns = [col[1] for col in cursor.fetchall()]

if "image" not in columns:
    cursor.execute("ALTER TABLE students ADD COLUMN image TEXT;")

# -----------------------------
# Sample Data (Add if not exists)
# -----------------------------

# Sample Routes
routes_data = [
    ("Campus Main Gate", "City Center", "Gate 1, Library, Cafeteria, City Stop 1, City Stop 2, City Center Plaza"),
    ("Hostel Block A", "Airport", "Hostel A, Academic Block, Sports Complex, Highway Entry, Airport Terminal 1, Airport Terminal 2"),
    ("Library", "Mall", "Library Entrance, Science Block, Engineering Block, Mall Parking, Mall Entrance, Food Court")
]

for start, end, stops in routes_data:
    cursor.execute("INSERT OR IGNORE INTO routes (start_point, end_point, stops) VALUES (?, ?, ?)", (start, end, stops))

# Sample Buses (2 buses, assigned to routes and drivers)
buses_data = [
    ("BUS-001", 1, 50),  # Assigned to route 1, capacity 50
    ("BUS-002", 2, 45),  # Route 2
]

for bus_num, route_id, capacity in buses_data:
    cursor.execute("INSERT OR IGNORE INTO buses (bus_number, route_id, capacity) VALUES (?, ?, ?)", (bus_num, route_id, capacity))

# Sample Drivers (2 drivers, assigned to buses)
drivers_data = [
    ("Ahmed Khan", "ahmed@example.com", "123", "03001234567", 1),  # Assigned to bus 1
    ("Sara Ali", "sara@example.com", "123", "03009876543", 2),     # Bus 2
]

for name, email, password, contact, bus_id in drivers_data:
    cursor.execute("INSERT OR IGNORE INTO drivers (name, email, password, contact, bus_id) VALUES (?, ?, ?, ?, ?)", (name, email, password, contact, bus_id))

# Update buses with driver_id (since bus_id in drivers refers to buses.id)
# But since we inserted with bus_id, and buses have ids 1-10, drivers have bus_id 1-6 assigned.

# But to make it correct, perhaps assign properly.
# For simplicity, the above should work if ids match.

# But to be safe, let's assign driver_id to buses.
# After inserting, update buses set driver_id = (select id from drivers where bus_id = buses.id)

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

# Sample Stops for routes (with approximate coordinates)
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

# Commit changes and close connection
conn.commit()
conn.close()

print("✅ Database and all tables created successfully with sample data!")
