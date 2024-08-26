from keras.models import load_model
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# Load the model from the HDF5 file
model = load_model('flight_path_predictor.keras')

# Load the training data to fit the scaler
df_train = pd.read_csv('flight_paths.csv')

# Normalize the features using the scaler
scaler = MinMaxScaler()
df_train[['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']] = scaler.fit_transform(
    df_train[['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']])

# Example input data
data = {
    'timestamp': [5],  # This is the time difference
    'latitude': [40.33151],
    'longitude': [42.58464],
    'altitude': [1135.03316],
    'heading': [254.085510],
    'speed': [344.0],
    'roll': [0],
    'pitch': [-0.1]
}
df = pd.DataFrame(data)

# Normalize the input data using the same scaler
df_normalized = scaler.transform(df[['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']])

seq_length = 1
feature_count = 8  # Number of features: latitude, longitude, altitude, heading, speed, roll, pitch, timestamp

# Extract the last seq_length waypoints
current_path = df_normalized[-seq_length:, :].reshape((1, seq_length, feature_count))  # Add batch dimension

# Make prediction
next_waypoint_normalized = model.predict(current_path)

# Inverse transform the predicted values (latitude and longitude)
next_waypoint = scaler.inverse_transform(np.concatenate([next_waypoint_normalized, 
                                                         np.zeros((next_waypoint_normalized.shape[0], feature_count - 2))], axis=1))[:, :2]

print("Predicted next waypoint (latitude, longitude):", next_waypoint)
