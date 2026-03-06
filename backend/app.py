from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample bus data
buses = [
    {"id": 1, "name": "University Bus 1", "lat": 30.1575, "lng": 71.5249},
    {"id": 2, "name": "University Bus 2", "lat": 30.1700, "lng": 71.5100}
]

# Home route
@app.route('/')
def home():
    return "Bus Tracking Backend Running!"

# API route
@app.route('/api/buses')
def get_buses():
    return jsonify(buses)

if __name__ == "__main__":
    app.run(debug=True)