import cv2
import time
import json
import requests
import numpy as np
from datetime import datetime
from ultralytics import YOLO
import os

# -----------------------------
# 서버 설정
# -----------------------------
SERVER_URL = "http://서버IP:8000/agv/upload_observation"

# -----------------------------
# YOLO 모델 로드
# -----------------------------
model = YOLO("best.pt")

# -----------------------------
# 카메라 초기화
# -----------------------------
cap = cv2.VideoCapture(0)
time.sleep(1)

# -----------------------------
# YOLO N회 실행
# -----------------------------
def yolo_multi_inference(N=5):
    confs, names = [], []
    last_frame = None

    for _ in range(N):
        ret, frame = cap.read()
        if not ret:
            continue

        last_frame = frame
        results = model(frame)
        boxes = results[0].boxes

        if len(boxes) == 0:
            continue

        box = boxes[0]
        cls_name = model.names[int(box.cls[0])]
        conf = float(box.conf[0])

        names.append(cls_name)
        confs.append(conf)
        time.sleep(0.2)

    if not names:
        return last_frame, "unknown", 0.0

    final_class = max(set(names), key=names.count)
    final_conf = float(np.mean([c for c, n in zip(confs, names) if n == final_class]))
    return last_frame, final_class, round(final_conf, 3)

# -----------------------------
# 정찰 사이클 시작
# -----------------------------
nodes = ["green", "purple", "blue", "orange"]
cycle_id = datetime.now().strftime("%Y_%m_%d_%H%M")
agv_id = "AGV1"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

observations = []
image_files = []

os.makedirs("images", exist_ok=True)

print(f"[AGV] Cycle {cycle_id} 시작")

for node in nodes:
    print(f"[AGV] {node} 도착")

    frame, result, conf = yolo_multi_inference()

    # 🔹 이미지 저장 (node 이름으로!)
    img_path = f"images/{node}.jpg"
    cv2.imwrite(img_path, frame)

    observations.append({
        "node": node,
        "image_url": "",
        "yolo": {
            "result": result,
            "confidence": conf
        }
    })

    image_files.append(
        ("images", (f"{node}.jpg", open(img_path, "rb"), "image/jpeg"))
    )

print("[AGV] 한 바퀴 완료 → 서버 전송")

# -----------------------------
# 서버로 보낼 payload (JSON 문자열)
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

# -----------------------------
# POST 전송 (JSON + 이미지 같이)
# -----------------------------
response = requests.post(
    SERVER_URL,
    data=data,
    files=image_files,
    timeout=30
)

print("[서버 응답]", response.status_code)
print(response.text)

cap.release()
cv2.destroyAllWindows()
