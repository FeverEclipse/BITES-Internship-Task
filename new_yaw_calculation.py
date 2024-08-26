import math
import numpy as np

def calculate_new_yaw(pitch, roll, prev_yaw):
    radpitch = np.radians(pitch)
    radroll = np.radians(roll)
    yaw_change = np.sin(radroll) * radpitch
    return prev_yaw + np.degrees(yaw_change)