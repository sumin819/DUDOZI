# stream_server.py
from flask import Flask, Response
import cv2
import time
from camera_manager import get_usb_frame

app = Flask(__name__)

_last_frame = None


def gen_usb_frames():
    global _last_frame
    last = time.time()
    count = 0

    while True:
        frame = get_usb_frame()

        if frame is not None:
            _last_frame = frame

            count += 1
            now = time.time()
            if now - last >= 1.0:
                print(f"[STREAM OUT] FPS: {count}")
                count = 0
                last = now

        # ✅ 프레임이 없을 때는 마지막 프레임 or 대기
        if _last_frame is None:
            time.sleep(0.05)
            continue

        _, jpeg = cv2.imencode(".jpg", _last_frame)
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + jpeg.tobytes()
            + b"\r\n"
        )

        # ✅ 과도한 전송 방지 (약 30fps cap)
        time.sleep(0.03)


@app.route("/usb_video")
def usb_video():
    return Response(
        gen_usb_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def run_stream_server():
    print("Stream server: USB Cam on /usb_video")
    app.run(host="0.0.0.0", port=5000, threaded=True)
