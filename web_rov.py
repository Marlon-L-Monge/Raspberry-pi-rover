from flask import Flask, render_template_string, request
import RPi.GPIO as GPIO
import socket
import time
import threading
import os

app = Flask(__name__)

# -------------------------
# Motor Pins (L298N)
# -------------------------
LEFT_IN1  = 17
LEFT_IN2  = 27
RIGHT_IN1 = 22
RIGHT_IN2 = 23

# -------------------------
# Ultrasonic Sensor Pins
# -------------------------
TRIG = 5
ECHO = 6

# -------------------------
# Config
# -------------------------
OBSTACLE_DISTANCE_CM = 20

# -------------------------
# GPIO Setup
# -------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in (LEFT_IN1, LEFT_IN2, RIGHT_IN1, RIGHT_IN2):
    GPIO.setup(pin, GPIO.OUT)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)

time.sleep(2)

# -------------------------
# Global Status
# -------------------------
current_action = "Stopped"

# -------------------------
# Motor Functions
# -------------------------
def move_forward():
    global current_action
    current_action = "Forward"

    GPIO.output(LEFT_IN1, GPIO.HIGH)
    GPIO.output(LEFT_IN2, GPIO.LOW)

    GPIO.output(RIGHT_IN1, GPIO.HIGH)
    GPIO.output(RIGHT_IN2, GPIO.LOW)

def move_backward():
    global current_action
    current_action = "Backward"

    GPIO.output(LEFT_IN1, GPIO.LOW)
    GPIO.output(LEFT_IN2, GPIO.HIGH)

    GPIO.output(RIGHT_IN1, GPIO.LOW)
    GPIO.output(RIGHT_IN2, GPIO.HIGH)

def turn_left():
    global current_action
    current_action = "Left"

    GPIO.output(LEFT_IN1, GPIO.LOW)
    GPIO.output(LEFT_IN2, GPIO.HIGH)

    GPIO.output(RIGHT_IN1, GPIO.HIGH)
    GPIO.output(RIGHT_IN2, GPIO.LOW)

def turn_right():
    global current_action
    current_action = "Right"

    GPIO.output(LEFT_IN1, GPIO.HIGH)
    GPIO.output(LEFT_IN2, GPIO.LOW)

    GPIO.output(RIGHT_IN1, GPIO.LOW)
    GPIO.output(RIGHT_IN2, GPIO.HIGH)

def stop():
    global current_action
    current_action = "Stopped"

    for pin in (LEFT_IN1, LEFT_IN2, RIGHT_IN1, RIGHT_IN2):
        GPIO.output(pin, GPIO.LOW)

# -------------------------
# Ultrasonic Sensor
# -------------------------
def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start = time.time()
    timeout = start + 0.04

    while GPIO.input(ECHO) == 0:
        start = time.time()
        if start > timeout:
            return None

    stop_time = time.time()

    while GPIO.input(ECHO) == 1:
        stop_time = time.time()
        if stop_time > timeout:
            return None

    distance = (stop_time - start) * 17150
    return round(distance, 2)

# -------------------------
# Pi Information
# -------------------------
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "Unknown"
    finally:
        s.close()

    return ip

def get_cpu_temp():
    try:
        temp = os.popen("vcgencmd measure_temp").readline()
        return temp.replace("temp=", "")
    except:
        return "Unavailable"

# -------------------------
# Web Page
# -------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi Rover</title>

    <style>
        body {
            background: #111;
            color: white;
            text-align: center;
            font-family: Arial;
        }

        button {
            width: 120px;
            height: 60px;
            margin: 10px;
            font-size: 20px;
            border-radius: 10px;
            border: none;
        }

        .forward { background: green; }
        .backward { background: red; }
        .left { background: orange; }
        .right { background: orange; }
        .stop { background: gray; }

        .info {
            margin: 20px;
            font-size: 20px;
        }
    </style>
</head>

<body>

    <h1>🚗 Raspberry Pi Rover</h1>

    <div class="info">
        <p><b>IP Address:</b> {{ ip }}</p>
        <p><b>CPU Temp:</b> {{ temp }}</p>
        <p><b>Status:</b> {{ action }}</p>
        <p><b>Distance:</b> {{ distance }} cm</p>
    </div>

    <form method="POST">

        <div>
            <button class="forward" name="command" value="forward">
                Forward
            </button>
        </div>

        <div>
            <button class="left" name="command" value="left">
                Left
            </button>

            <button class="stop" name="command" value="stop">
                Stop
            </button>

            <button class="right" name="command" value="right">
                Right
            </button>
        </div>

        <div>
            <button class="backward" name="command" value="backward">
                Backward
            </button>
        </div>

    </form>

</body>
</html>
"""

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET", "POST"])
def home():

    distance = get_distance()

    if request.method == "POST":

        command = request.form["command"]

        # Obstacle protection
        if command == "forward":

            if distance is not None and distance < OBSTACLE_DISTANCE_CM:
                stop()
                current = "Obstacle Detected!"
            else:
                move_forward()

        elif command == "backward":
            move_backward()

        elif command == "left":
            turn_left()

        elif command == "right":
            turn_right()

        elif command == "stop":
            stop()

    return render_template_string(
        HTML,
        ip=get_ip(),
        temp=get_cpu_temp(),
        action=current_action,
        distance=distance
    )

# -------------------------
# Cleanup
# -------------------------
def cleanup():
    stop()
    GPIO.cleanup()

# -------------------------
# Start Server
# -------------------------
if __name__ == "__main__":

    try:
        print("Starting Rover Web Server...")
        print(f"Open browser to: http://{get_ip()}:5000")

        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False
        )

    finally:
        cleanup()