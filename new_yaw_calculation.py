import math
import numpy as np

def calculate_new_yaw(pitchrate, roll, prev_yaw):
    radpitchrate = np.radians(pitchrate)
    radroll = np.radians(roll)
    yaw_change = np.sin(radroll) * radpitchrate
    return prev_yaw + np.degrees(yaw_change)