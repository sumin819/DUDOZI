# servo_controller.py
from SCSCtrl import TTLServo

LINE_FOLLOW_SERVO_ID = 5
LINE_FOLLOW_ANGLE = -50

def set_line_follow_pose():
    TTLServo.servoAngleCtrl(
        LINE_FOLLOW_SERVO_ID,
        LINE_FOLLOW_ANGLE,
        1,      # speed
        100     # time
    )
    print("[SERVO] Line-follow pose set")
