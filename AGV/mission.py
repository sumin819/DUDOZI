# mission.py 수정본
import threading
import time
from camera_manager import get_frame
from steering_model import infer_xy
from line_follow import LineFollower
from motor_controller import drive, stop
from servo_controller import set_line_follow_pose

_running = False
_mission_thread = None # 미션 스레드 관리를 위한 변수

follower = LineFollower(
    speed_gain=0.15,
    steering_gain=0.12,
    steering_dgain=0.0,
    steering_bias=0.0,
)

def _mission_loop():
    print("[MISSION] Running (no control, stream only)")
    while _running:
        time.sleep(0.1)
    print("[MISSION] Stopped")


def start_mission(cycle_id):
    global _running, _mission_thread

    if _running:
        return

    print(f"[MISSION] START {cycle_id}")
    _running = True

    _mission_thread = threading.Thread(
        target=_mission_loop,
        daemon=True
    )
    _mission_thread.start()


def stop_mission():
    global _running
    print("[MISSION] STOP")
    _running = False