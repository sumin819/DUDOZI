# motor_controller.py
from jetbot import Robot

robot = Robot()

def drive(steering, speed):
    left = max(min(speed + steering, 1.0), 0.0)
    right = max(min(speed - steering, 1.0), 0.0)
    robot.left_motor.value = left
    robot.right_motor.value = right

def stop():
    robot.stop()
