import requests, time, random

API_URL = "http://127.0.0.1:5000/update_location"

latitude = 24.8607
longitude = 67.0011

while True:
    latitude += random.uniform(-0.0005, 0.0005)
    longitude += random.uniform(-0.0005, 0.0005)
    data = {"latitude": latitude, "longitude": longitude}
    try:
        res = requests.post(API_URL, json=data)
        print("Location Sent:", res.json())
    except:
        print("Server error!")
    time.sleep(5)