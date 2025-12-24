# line_follow.py
import numpy as np

class LineFollower:
    def __init__(
        self,
        speed_gain=0.15,
        steering_gain=0.15,
        steering_dgain=0.0,
        steering_bias=0.0,
    ):
        self.speed_gain = speed_gain
        self.steering_gain = steering_gain
        self.steering_dgain = steering_dgain
        self.steering_bias = steering_bias
        self.angle_last = 0.0

    def compute(self, x, y):
        y = (0.5 - y) / 2.0
        angle = np.arctan2(x, y)

        pid = (
            angle * self.steering_gain
            + (angle - self.angle_last) * self.steering_dgain
        )
        self.angle_last = angle

        steering = pid + self.steering_bias
        speed = self.speed_gain

        return steering, speed
