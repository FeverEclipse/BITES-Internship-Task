import math

def update_position(lat, lon, velocity, heading, time_interval):
    distance_traveled = (velocity / 3600) * time_interval
    heading_rad = math.radians(heading)
    delta_lat = distance_traveled * math.cos(heading_rad) / 60
    delta_lon = (distance_traveled * math.sin(heading_rad) / (60 * math.cos(math.radians(lat)))) * -1
    new_lat = lat + delta_lat
    new_lon = lon + delta_lon
    return new_lat, new_lon