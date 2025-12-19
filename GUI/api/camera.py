import cv2
import requests
from PySide6.QtGui import QImage, QPixmap

SERVER_URL = "http://localhost:8000"
AGV_ID = "AGV1"

# --------------------------------
# 이동 명령
# --------------------------------
def send_move(self, direction: str):
    try:
        requests.post(
            f"{SERVER_URL}/agv/manual_move",
            json={
                "agv_id": AGV_ID,
                "direction": direction
            },
            timeout=0.2
        )
    except Exception as e:
        print("Move failed:", e)

# --------------------------------
# 카메라 프레임 업데이트 (GUI 호출)
# --------------------------------
def update_camera(self):
    if not self.cap:
        return

    ret, frame = self.cap.read()
    if not ret:
        return

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    self.ui.cameraView.setPixmap(QPixmap.fromImage(img))
