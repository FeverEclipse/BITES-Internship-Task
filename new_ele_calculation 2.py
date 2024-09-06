import numpy as np

def calculate_new_elevation(previous_elevation, pitch, velocity, dt):
    pitch_rad = np.radians(pitch)
    vertical_velocity = velocity * np.sin(pitch_rad)
    delta_elevation = vertical_velocity * dt
    new_elevation = previous_elevation + delta_elevation
    return new_elevation
