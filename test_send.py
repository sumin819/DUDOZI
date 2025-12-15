import requests
import json

url = "http://127.0.0.1:8000/agv/upload_observation"

payload = {
    "cycle_id": "2025_12_09_1630",
    "agv_id": "AGV1",
    "timestamp": "2025-12-15 17:10:00",
    "observations": [
        {"node": "green",  "yolo": {"result": "unknown", "confidence": 0.0}},
        {"node": "purple", "yolo": {"result": "unknown", "confidence": 0.0}},
        {"node": "blue",   "yolo": {"result": "unknown", "confidence": 0.0}},
        {"node": "orange", "yolo": {"result": "unknown", "confidence": 0.0}}
    ]
}

files = [
    ("images", ("green.jpg",  open("green.jpg", "rb"),  "image/jpeg")),
    ("images", ("purple.jpg", open("purple.jpg", "rb"), "image/jpeg")),
    ("images", ("blue.jpg",   open("blue.jpg", "rb"),   "image/jpeg")),
    ("images", ("orange.jpg", open("orange.jpg", "rb"), "image/jpeg")),
]

data = {"payload": json.dumps(payload)}

res = requests.post(url, data=data, files=files)
print(res.status_code)
print(res.json())