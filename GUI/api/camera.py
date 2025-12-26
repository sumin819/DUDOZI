import cv2
import requests
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
import numpy as np
from api.stream_thread import MJPEGStreamThread

# SERVER_URL = "http://127.0.0.1:8000"
SERVER_URL = "http://172.20.10.6:8888"
AGV_STREAM_URL = "http://172.20.10.10:5000/usb_video"
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
def start_camera_stream(self):
    if hasattr(self, "stream_thread"):
        return

    print("Connecting to AGV camera stream")

    self.stream_thread = MJPEGStreamThread(AGV_STREAM_URL)
    self.stream_thread.frame_received.connect(
        lambda frame: update_camera_frame(self, frame)
    )
    self.stream_thread.error.connect(
        lambda e: print("[STREAM ERROR]", e)
    )
    self.stream_thread.start()


def update_camera_frame(self, frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    self.ui.cameraView.setPixmap(QPixmap.fromImage(img))


def stop_camera_stream(self):
    if hasattr(self, "stream_thread"):
        self.stream_thread.stop()
        del self.stream_thread

    self.ui.cameraView.setText("SYSTEM OFF")
