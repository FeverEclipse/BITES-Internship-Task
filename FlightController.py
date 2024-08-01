import tkinter as tk
from pynput import keyboard
import serial
import threading
import time

ser = serial.Serial(
    port='/dev/ttys015',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=100,
    xonxoff=0,
    rtscts=0
    )

gui = tk.Tk()
gui.title = "BITES Flight Controller"

def pressHandler(event = None):
    global pitch_val
    global roll_val
    global acc_val
    if event.char == 'w':
        pitch_val.set(-10)
    elif event.char == 's':
        pitch_val.set(10)
    elif event.char == 'a':
        roll_val.set(-10)
    elif event.char == 'd':
        roll_val.set(10)
    else:
        try:
            acc_val.set(int(event.char))
        except:
            print('undefined key pressed.')

def releaseHandler(event = None):
    global pitch_val
    global roll_val
    global acc_val
    if event.char == 'w' or event.char == 's':
        pitch_val.set(0)
    elif event.char == 'a' or event.char == 'd':
        roll_val.set(0)

def startFlying():
    global ser
    global start_button
    global roll_slider
    global pitch_slider
    global acc_slider
    global roll_val
    global pitch_val
    global acc_val
    ser.write(b"\x01\x00\x00\x00")
    time.sleep(0.01)
    start_button.config(text="Waiting for taxiing", state=tk.DISABLED)
    ReceivedData = b""
    while ser.inWaiting() < 1:
        time.sleep(0.01) # Read bytes from the device until finished
    ReceivedData += ser.read(1)
    if ReceivedData == b"\x11":
        start_button.config(text="Ready!")
    roll_slider.config(state=tk.ACTIVE)
    pitch_slider.config(state=tk.ACTIVE)
    acc_slider.config(state=tk.ACTIVE)
    sendData()

def sendData():
    global roll_val
    global pitch_val
    global acc_val
    while True:
        data = b"\x01"
        bAcc = acc_val.get().to_bytes(1, 'big')

        if roll_val.get() == 0:
            bRoll = b"\x00"
        elif roll_val.get() > 0:
            bRoll = b"\x01"
        else:
            bRoll = b"\x02"

        if pitch_val.get() == 0:
            bPitch = b"\x00"
        elif pitch_val.get() > 0:
            bPitch = b"\x01"
        else:
            bPitch = b"\x02"
        data += bAcc + bRoll + bPitch
        ser.write(data)
        time.sleep(1/60)

def startFlyThread():
    flythread = threading.Thread(target=startFlying, daemon=True)
    flythread.start()
    

start_button = tk.Button(gui,text="Start the Plane", command=startFlyThread)
start_button.grid(row=0, columnspan=3, pady=10)

roll_label = tk.Label(gui,text='Roll')
roll_label.grid(row=2,column=0)

roll_val = tk.IntVar(gui,value=0)
roll_slider = tk.Scale(gui, from_=-10, to=10, orient='horizontal', variable=roll_val, state=tk.DISABLED)
roll_slider.grid(row=1,column=0, padx=50)

pitch_label = tk.Label(gui, text="Pitch")
pitch_label.grid(row=2, column=1, padx=50)

pitch_val = tk.IntVar(gui,value=0)
pitch_slider = tk.Scale(gui, from_=-10, to=10, orient='vertical', variable=pitch_val, state=tk.DISABLED)
pitch_slider.grid(row=1, column=1, padx=50)

acc_label = tk.Label(gui, text="Acceleration/\nEngine Power")
acc_label.grid(row=2, column=2)

acc_val = tk.IntVar(gui,value=0)
acc_slider = tk.Scale(gui, from_=9, to=0, orient='vertical', variable=acc_val, state=tk.DISABLED)
acc_slider.grid(row=1, column=2, padx=50)


gui.bind('<KeyPress>', pressHandler)
gui.bind('<KeyRelease>', releaseHandler)

gui.mainloop()