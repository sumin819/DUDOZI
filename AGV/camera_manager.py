# camera_manager.py
import cv2
from jetbot import Camera
import time

_camera = None       # CSI 카메라 (라인트레이싱용)
_usb_camera = None   # USB 웹캠 (GUI 출력 전용)

# camera_manager.py (USB 부분만)
import cv2

_usb_camera = None

def system_on():
    global _usb_camera

    if _usb_camera is not None:
        return

    gst_pipeline = (
        "v4l2src device=/dev/video1 ! "
        "image/jpeg, width=640, height=480, framerate=30/1 ! "
        "jpegdec ! videoconvert ! "
        "appsink drop=true sync=false max-buffers=1"
    )

    _usb_camera = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

    if _usb_camera.isOpened():
        print("USB Webcam (GStreamer MJPG) ON")
    else:
        print("Failed to open USB Webcam via GStreamer")
        _usb_camera = None


def system_off():
    global _camera, _usb_camera

    if _camera:
        _camera.stop()
        _camera = None

    if _usb_camera:
        _usb_camera.release()
        _usb_camera = None

    print("All Cameras OFF")

def get_frame():
    """CSI 카메라 (라인트레이싱)"""
    return _camera.value if _camera else None

# FPS 체크용
_last_time = time.time()
_frame_count = 0

def get_usb_frame():
    global _last_time, _frame_count

    if _usb_camera and _usb_camera.isOpened():
        ret, frame = _usb_camera.read()
        if not ret:
            return None

        _frame_count += 1
        now = time.time()

        if now - _last_time >= 1.0:
            print(f"[USB CAM] FPS: {_frame_count}")
            _frame_count = 0
            _last_time = now

        return frame

    return None