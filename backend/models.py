from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))

class Bus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.String(10))
    driver_name = db.Column(db.String(50))
    route = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    speed = db.Column(db.Float)
    status = db.Column(db.String(10))  # active/inactive

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    start = db.Column(db.String(50))
    end = db.Column(db.String(50))