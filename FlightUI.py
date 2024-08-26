import time
import speedometer
import compass
import roll
import serial
import threading
import os
import tkintermapview
import new_ele_calculation
import new_yaw_calculation
import pandas as pd
import updateLocation
from PIL import Image, ImageTk
import tkinter as tk
from keras.models import load_model
import numpy as np
from sklearn.preprocessing import MinMaxScaler

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BITES Flight UI")
        
        self.start_time = time.time()

        self.curlat = 40.33151
        self.curlon = 42.58464

        self.map_widget = tkintermapview.TkinterMapView(self, width=900, height=250, corner_radius=0)
        self.map_widget.grid(row=0, columnspan=3)
        self.current_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        plane_image = ImageTk.PhotoImage(Image.open(os.path.join(self.current_path, "assets", "plane_icon.png")).resize((40, 40)))
        self.marker_1 = self.map_widget.set_marker(self.curlat, self.curlon, text="BITES Aircraft", icon=plane_image)
        self.map_widget.set_position(self.curlat,self.curlon)
        self.map_widget.set_zoom(10)

        self.message_frame = tk.Frame(self, width=600, height=50)
        self.message_frame.grid(row=1, column=1)

        self.marker_2 = None
        self.marker_3 = None
        self.flap_Val = False
        
        self.message_icon = ImageTk.PhotoImage(Image.open("assets/message_icon_white.png").resize([30,30]))
        self.message_icon_label = tk.Label(self.message_frame, image=self.message_icon)
        self.message_icon_label.grid(row=1,column=0)

        self.pitch_val = tk.StringVar(self, "Pitch: 0deg")
        self.pitch_text = tk.Label(self, textvariable=self.pitch_val)
        self.pitch_text.grid(row=1,column=0)

        self.message_text = tk.Label(self.message_frame, text="Messages will be shown here.")
        self.message_text.grid(row=1,column=1)

        self.feet_val = tk.StringVar(self, "Elevation: 0 feet")
        self.feet_text = tk.Label(self, textvariable=self.feet_val)
        self.feet_text.grid(row=1, column=2)

        self.status_val = tk.StringVar(self, "STATUS")
        self.status_text = tk.Label(self, textvariable=self.status_val, font=("Segoe UI Bold", 36))
        self.status_text.grid(row=3, columnspan=3)

        self.controls_frame = tk.Frame(self,width=900, height=300)
        self.controls_frame.grid(row=2, columnspan=3)
        # Create frames for each view
        self.compass_frame = tk.Frame(self.controls_frame, width=300, height=300)
        self.compass_frame.grid(row=2, column=1)
        
        self.roll_frame = tk.Frame(self.controls_frame, width=300, height=300)
        self.roll_frame.grid(row=2, column=0)
        
        self.speedometer_frame = tk.Frame(self.controls_frame, width=300, height=300)
        self.speedometer_frame.grid(row=2, column=2)

        # Initialize the views
        self.load_compass_view()
        self.load_roll_view()
        self.load_speedometer_view()

    def connect_serial(self):
        self.ser = serial.Serial(
            port='/dev/ttys018',
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=100,
            xonxoff=0,
            rtscts=0
            )
        
    def load_compass_view(self):
        self.compass_instance = compass.RotatingCompass(self.compass_frame)
        self.compass_instance.pack(expand=True, fill='both')

    def load_roll_view(self):
        self.roll_instance = roll.Roll(self.roll_frame)
        self.roll_instance.pack(expand=True, fill='both')

    def load_speedometer_view(self):
        self.speedometer_instance = speedometer.AnalogSpeedometer(self.speedometer_frame)
        self.speedometer_instance.pack(expand=True, fill='both')

def communicationHandler():
    global app
    global isStarted
    global velocity
    global pitch
    global rollvalue
    global elevation
    global heading
    global flight_data
    drawn = 0
    location_icon = ImageTk.PhotoImage(Image.open(os.path.join(app.current_path, "assets", "location_icon.png")).resize((10, 10)))
    while True:
        ReceivedData = b""
        while app.ser.inWaiting() < 5:
            time.sleep(0.01) # Read bytes from the device until finished
        ReceivedData += app.ser.read(5)
        decoded = ''.join(f'{byte:02X}' for byte in ReceivedData)
        bStart = int(decoded[0:2], 16)
        if bStart == 1 and not isStarted:
            isStarted = True
            app.status_val.set("TAXIING")
            app.status_text.config(fg="#ff0")
            #time.sleep(5)
            app.ser.write(b"\x11")
            app.status_val.set("READY FOR TAKEOFF")
            app.status_text.config(fg="#0f0")
        elif isStarted:
            accVal = int(decoded[2:4], 16)
            rollVal = int(decoded[4:6], 16)
            pitchVal = int(decoded[6:8], 16)
            flapval = int(decoded[8:10], 16)

            if pitchVal == 2 and app.status_val.get() != "FLYING":
                app.message_text.config(text="Cannot enter negative pitch when not flying!", fg="#f00")
            elif pitchVal == 2 and pitch <= -90:
                app.message_text.config(text="Reached Minimum Pitch!", fg="#f00")
            elif pitchVal == 2:
                pitch -= 0.8
            elif pitchVal == 1 and elevation == 0 and velocity < 150:
                app.message_text.config(text="Cannot lift without enough speed!", fg="#f00")
            elif pitchVal == 1 and elevation >= 50000:
                app.message_text.config(text="Reached Maximum Elevation!", fg="#f00")
            elif pitchVal == 1 and pitch >= 90:
                app.message_text.config(text="Reached Maximum Pitch!", fg="#f00")
            elif pitchVal == 1 and elevation < 50000:
                pitch += 0.8
            elif pitch > 0:
                pitch -= 0.4
            elif pitch < 0:
                pitch += 0.4
            
            if (rollVal == 1 or rollVal == 2) and app.status_val.get() != "FLYING":
                app.message_text.config(text="Cannot roll when not flying!", fg="#f00")
            elif rollVal == 2 and rollvalue == 90:
                app.message_text.config(text="Reached maximum roll!", fg="#f00")
            elif rollVal == 2:
                rollvalue += 0.5 if (rollvalue + 0.5) <= 90 else 0
            elif rollVal == 1 and rollvalue == -90:
                app.message_text.config(text="Reached maximum roll", fg="#f00")
            elif rollVal == 1:
                rollvalue -= 0.5 if (rollvalue - 0.5) >= -90 else 0
            elif rollvalue > 0:
                rollvalue -= 0.5
            elif rollvalue < 0:
                rollvalue += 0.5

            if app.status_val.get() != "CRASHED" and app.status_val.get() != "LANDED":
                if accVal == 0 and velocity > 0:
                    velocity -= 0.5
                elif velocity < 900:
                    velocity += accVal
                elif velocity >= 900:
                    velocity = 900
                    app.message_text.config(text="Reached maximum speed!", fg="#f00")
            
            if flapval == 1 and app.status_val.get() == "FLYING":
                if velocity > 500:
                    velocity -= 7
                else:
                    velocity -= 4 if velocity - 4 >= 0 else 0
            elif flapval == 1 and app.status_val.get() != "FLYING":
                app.message_text.config(text="Cannot open flaps when not flying!", fg="#f00")

            if len(flight_data) > drawn:
                app.marker_2 = app.map_widget.set_marker(flight_data[-1]['latitude'], flight_data[-1]['longitude'], icon=location_icon)
                drawn += 1

            cur_time = time.time()

            new_ele = new_ele_calculation.calculate_new_elevation(elevation, pitch, velocity,(cur_time - app.start_time))
            new_yaw = new_yaw_calculation.calculate_new_yaw(pitch,rollvalue,heading)

            if new_yaw > 360 or new_yaw < -360:
                new_yaw = 0

            elevation = new_ele if new_ele > 0 else 0
            heading = new_yaw
            app.curlat, app.curlon = updateLocation.update_position(app.curlat,app.curlon,velocity,heading,(cur_time - app.start_time))

            bounding_lat_upper = app.curlat + 0.05
            bounding_lon_lower = app.curlon - 0.05
            bounding_lat_lower = app.curlat - 0.05
            bounding_lon_upper = app.curlon + 0.05

            if app.status_val.get() == "READY FOR TAKEOFF" and elevation > 0 and velocity > 150 and pitch > 0:
                app.status_val.set("FLYING")
                app.message_text.config(text="Messages will be shown here.", fg="#fff")
            elif app.status_val.get() == "FLYING" and elevation == 0 and velocity > 100 and pitch < 0:
                app.status_val.set("CRASHED")
                app.status_text.config(fg="#f00")
            elif app.status_val.get() == "FLYING" and elevation == 0 and velocity < 100 and pitch < 10 and pitch > -10:
                app.status_val.set("LANDED")
            if app.status_val.get() == "CRASHED":
                velocity = 0

            if app.marker_3 != None:
                if app.marker_3.data[0] > app.curlat + 0.05:
                    bounding_lat_upper = app.marker_3.data[0] + 0.05
                    bounding_lat_lower = app.curlat - (app.marker_3.data[0] - app.curlat) - 0.05
                elif app.marker_3.data[0] < app.curlat - 0.05:
                    bounding_lat_lower = app.marker_3.data[0] - 0.05
                    bounding_lat_upper = app.curlat + (app.curlat - app.marker_3.data[0]) + 0.05
                if app.marker_3.data[1] > app.curlon + 0.05:
                    bounding_lon_upper = app.marker_3.data[1] + 0.05
                    bounding_lon_lower = app.curlon - (app.marker_3.data[1] - app.curlon) - 0.05
                elif app.marker_3.data[1] < app.curlon - 0.05:
                    bounding_lon_lower = app.marker_3.data[1] - 0.05
                    bounding_lon_upper = app.curlon + (app.curlon - app.marker_3.data[1]) + 0.05

            #app.map_widget.set_position(app.curlat, app.curlon)
            app.map_widget.fit_bounding_box([bounding_lat_upper, bounding_lon_lower], [bounding_lat_lower, bounding_lon_upper])
            app.marker_1.set_position(app.curlat, app.curlon)

            app.feet_val.set("Elevation: " + str(int(elevation)) + " feet")
            app.compass_instance.rotate_needle(new_yaw)
            
            app.roll_instance.rotate_needle(rollvalue)
            app.pitch_val.set("Pitch: " + str(int(pitch)) + "deg")
            app.speedometer_instance.rotate_needle(velocity)

            app.start_time = time.time()


def dataSaver():
    global app
    global velocity
    global pitch
    global rollvalue
    global elevation
    global heading
    global flight_data
    while True:
        flight_data.append({
        'timestamp': 5,
        'latitude': app.curlat,
        'longitude': app.curlon,
        'altitude': elevation,
        'heading': heading,
        'speed': velocity,
        'roll': rollvalue,
        'pitch': pitch
        })
        df = pd.DataFrame([flight_data[-1]])
        df.to_csv('flight_paths.csv', index=False, mode="a", header=False)
        time.sleep(5)

def pathPredictor():
    global flight_data
    global app
    directory = app.current_path
    target_icon = ImageTk.PhotoImage(Image.open(os.path.join(directory, "assets", "target_icon.png")).resize((10, 10)))
    while True:
        model = load_model('flight_path_predictor.keras')
        df_train = pd.read_csv('flight_paths.csv')
        scaler = MinMaxScaler()
        df_train[['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']] = scaler.fit_transform(
         df_train[['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']])
        df = pd.DataFrame(flight_data)
        print("length of flight data: " , len(flight_data))
        df_normalized = scaler.transform(df[['latitude', 'longitude', 'altitude', 'heading', 'speed', 'roll', 'pitch', 'timestamp']])
        current_path = df_normalized[-len(flight_data):, :].reshape((1, len(flight_data), 8))
        next_waypoint_normalized = model.predict(current_path)
        next_waypoint = scaler.inverse_transform(np.concatenate([next_waypoint_normalized, 
                                                         np.zeros((next_waypoint_normalized.shape[0], 8 - 2))], axis=1))[:, :2]
        print("Predicted next waypoint (latitude, longitude):", next_waypoint)
        if app.marker_3 != None:
            app.marker_3.delete()
            app.marker_3 = None
        app.marker_3 = app.map_widget.set_marker(next_waypoint[0][0], next_waypoint[0][1], icon=target_icon, text="Predicted Point", data= [next_waypoint[0][0], next_waypoint[0][1]])
        time.sleep(5)
            

if __name__ == "__main__":
    app = tk.Tk
    app = MainWindow()
    flight_data = []
    isStarted = False
    app.resizable(False, False)
    velocity = 0.0
    pitch = 0.0
    rollvalue = 0.0
    elevation = 0.0
    heading = 0.0
    app.connect_serial()
    comm_thread = threading.Thread(target=communicationHandler)
    comm_thread.start()
    data_thread = threading.Thread(target=dataSaver)
    data_thread.start()
    ml_thread = threading.Thread(target=pathPredictor)
    ml_thread.start()
    app.mainloop()