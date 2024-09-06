import time
import speedometer
import compass
import roll
import serial
import threading
import new_ele_calculation
import new_yaw_calculation
from PIL import Image, ImageTk
import tkinter as tk

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BITES Flight UI")

        self.message_frame = tk.Frame(self, width=600, height=50)
        self.message_frame.grid(row=0, column=1)
        
        self.message_icon = ImageTk.PhotoImage(Image.open("assets/message_icon_white.png").resize([30,30]))
        self.message_icon_label = tk.Label(self.message_frame, image=self.message_icon)
        self.message_icon_label.grid(row=0,column=0)

        self.pitch_val = tk.StringVar(self, "Pitch: 0deg")
        self.pitch_text = tk.Label(self, textvariable=self.pitch_val)
        self.pitch_text.grid(row=0,column=0)

        self.message_text = tk.Label(self.message_frame, text="Messages will be shown here.")
        self.message_text.grid(row=0,column=1)

        self.feet_val = tk.StringVar(self, "Elevation: 0 feet")
        self.feet_text = tk.Label(self, textvariable=self.feet_val)
        self.feet_text.grid(row=0, column=2)

        self.status_val = tk.StringVar(self, "STATUS")
        self.status_text = tk.Label(self, textvariable=self.status_val, font=("Segoe UI Bold", 36))
        self.status_text.grid(row=2, columnspan=3)

        self.controls_frame = tk.Frame(self,width=900, height=300)
        self.controls_frame.grid(row=1, columnspan=3)
        # Create frames for each view
        self.compass_frame = tk.Frame(self.controls_frame, width=300, height=300)
        self.compass_frame.grid(row=1, column=1)
        
        self.roll_frame = tk.Frame(self.controls_frame, width=300, height=300)
        self.roll_frame.grid(row=1, column=0)
        
        self.speedometer_frame = tk.Frame(self.controls_frame, width=300, height=300)
        self.speedometer_frame.grid(row=1, column=2)

        # Initialize the views
        self.load_compass_view()
        self.load_roll_view()
        self.load_speedometer_view()

    def connect_serial(self):
        self.ser = serial.Serial(
            port='/dev/ttys016',
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
    while True:
        ReceivedData = b""
        while app.ser.inWaiting() < 4:
            time.sleep(0.01) # Read bytes from the device until finished
        ReceivedData += app.ser.read(4)
        decoded = ''.join(f'{byte:02X}' for byte in ReceivedData)
        bStart = int(decoded[0:2], 16)
        if bStart == 1 and not isStarted:
            isStarted = True
            app.status_val.set("TAXIING")
            app.status_text.config(fg="#ff0")
            #time.sleep(5)
            app.ser.write(b"\x11")
            app.status_val.set("READY")
            app.status_text.config(fg="#0f0")
        else:
            accVal = int(decoded[2:4], 16)
            rollVal = int(decoded[4:6], 16)
            pitchVal = int(decoded[6:8], 16)

            pitchstatus = 0

            if pitchVal == 2:
                pitch -= 0.2
                pitchstatus = -0.2
            elif pitchVal == 1:
                pitch += 0.2
                pitchstatus = 0.2
            elif pitch > 0:
                pitch -= 0.1
            elif pitch < 0:
                pitch += 0.1
            
            if rollVal == 2:
                rollvalue += 0.5
            elif rollVal == 1:
                rollvalue -= 0.5
            elif rollvalue > 0:
                rollvalue -= 0.5
            elif rollvalue < 0:
                rollvalue += 0.5

            if velocity < 900:
                velocity += accVal
            elif accVal == 0 and velocity > 0:
                velocity -= 0.5
            elif velocity >= 900:
                velocity = 900
                app.message_text.config(text="Reached maximum speed!", fg="#f00")

            new_ele = new_ele_calculation.calculate_new_elevation(elevation, pitch, velocity,1/60)
            new_yaw = new_yaw_calculation.calculate_new_yaw(pitchstatus,rollvalue,heading)

            elevation = new_ele if new_ele > 0 else 0
            heading = new_yaw

            app.feet_val.set("Elevation: " + str(int(elevation)) + " feet")
            app.compass_instance.rotate_needle(new_yaw)
            
            app.roll_instance.rotate_needle(rollvalue)
            app.pitch_val.set("Pitch: " + str(int(pitch)) + "deg")
            app.speedometer_instance.rotate_needle(velocity)
            


if __name__ == "__main__":
    app = MainWindow()
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
    app.mainloop()