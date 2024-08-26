import pandas as pd
import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# Load the flight data from the CSV file
df = pd.read_csv('flight_paths.csv')

# Normalize the features using the timestamp column directly
scaler = MinMaxScaler()
df[['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']] = scaler.fit_transform(
    df[['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']])

def create_sequences(data, seq_length):
    sequences = []
    targets = []
    for i in range(len(data) - seq_length):
        sequence = data.iloc[i:i+seq_length][['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']].values
        target = data.iloc[i+seq_length][['latitude', 'longitude']].values  # Predicting next latitude, longitude
        sequences.append(sequence)
        targets.append(target)
    return np.array(sequences), np.array(targets)

seq_length = 10  # Number of past waypoints to use for predicting the next
X, y = create_sequences(df, seq_length)

# Build the model
def build_model(seq_length, feature_count):
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(seq_length, feature_count)))
    model.add(LSTM(50))
    model.add(Dense(2))  # Predicting latitude and longitude
    model.compile(optimizer='adam', loss='mse')
    return model

feature_count = X.shape[2]  # Number of features (latitude, longitude, altitude, heading, speed, roll, pitch, timestamp)
model = build_model(seq_length, feature_count)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test))

# Save the model
model.save('flight_path_predictor.keras')
