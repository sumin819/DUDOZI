import json
import requests
from datetime import datetime
from ultralytics import YOLO
import os

# -----------------------------
# 서버 주소 (팀장 PC IP로 수정!)
# -----------------------------
SERVER_URL = "http://172.20.10.6:8888/agv/upload_observation"
# SERVER_URL = "http://127.0.0.1:8000/agv/upload_observation"


# -----------------------------
# 경로 설정
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------
# YOLO 모델 로드
# -----------------------------
model = YOLO(os.path.join(BASE_DIR, "best.pt"))

# -----------------------------
# 테스트 이미지 목록
# -----------------------------
nodes = ["green", "purple", "blue", "red"]

cycle_id = datetime.now().strftime("%Y_%m_%d_%H%M")
agv_id = "AGV1"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

observations = []
image_files = []

print(f"[AGV] Cycle {cycle_id} 시작")

for node in nodes:
    img_path = os.path.join(BASE_DIR, f"{node}.jpg")

    # -----------------------------
    # YOLO 추론 (1회만)
    # -----------------------------
    results = model(img_path)
    boxes = results[0].boxes

    if len(boxes) == 0:
        result = "unknown"
        conf = 0.0
    else:
        box = boxes[0]
        result = model.names[int(box.cls[0])]
        conf = round(float(box.conf[0]), 3)

    observations.append({
        "node": node,
        "yolo": {
            "result": result,
            "confidence": conf
        }
    })

    image_files.append(
        ("images", (f"{node}.jpg", open(img_path, "rb"), "image/jpeg"))
    )

    print(f"[AGV] {node}: {result}, conf={conf}")

# -----------------------------
# payload 생성 (image_url 없음!)
# -----------------------------
payload = {
    "cycle_id": cycle_id,
    "agv_id": agv_id,
    "timestamp": timestamp,
    "observations": observations
}

data = {
    "payload": json.dumps(payload, ensure_ascii=False)
}

print("[AGV] 서버로 전송 중...")

response = requests.post(
    SERVER_URL,
    data=data,
    files=image_files,
    timeout=30
)

print("[서버 응답]", response.status_code)
print(response.text)