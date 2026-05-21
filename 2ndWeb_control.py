from flask import Flask, Response, render_template_string
import RPi.GPIO as GPIO
import cv2
import time

# ==========================================
# FLASK APP
# ==========================================
app = Flask(__name__)

# ==========================================
# MOTOR PINS (L298N)
# ==========================================
LEFT_IN1  = 17
LEFT_IN2  = 27
RIGHT_IN1 = 22
RIGHT_IN2 = 23

# ==========================================
# GPIO SETUP
# ==========================================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

motor_pins = [
    LEFT_IN1,
    LEFT_IN2,
    RIGHT_IN1,
    RIGHT_IN2
]

for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# ==========================================
# MOTOR FUNCTIONS
# ==========================================
def stop():
    for pin in motor_pins:
        GPIO.output(pin, GPIO.LOW)

def forward():
    GPIO.output(LEFT_IN1, GPIO.HIGH)
    GPIO.output(LEFT_IN2, GPIO.LOW)

    GPIO.output(RIGHT_IN1, GPIO.HIGH)
    GPIO.output(RIGHT_IN2, GPIO.LOW)

def backward():
    GPIO.output(LEFT_IN1, GPIO.LOW)
    GPIO.output(LEFT_IN2, GPIO.HIGH)

    GPIO.output(RIGHT_IN1, GPIO.LOW)
    GPIO.output(RIGHT_IN2, GPIO.HIGH)

def left():
    GPIO.output(LEFT_IN1, GPIO.LOW)
    GPIO.output(LEFT_IN2, GPIO.HIGH)

    GPIO.output(RIGHT_IN1, GPIO.HIGH)
    GPIO.output(RIGHT_IN2, GPIO.LOW)

def right():
    GPIO.output(LEFT_IN1, GPIO.HIGH)
    GPIO.output(LEFT_IN2, GPIO.LOW)

    GPIO.output(RIGHT_IN1, GPIO.LOW)
    GPIO.output(RIGHT_IN2, GPIO.HIGH)

# ==========================================
# USB CAMERA
# ==========================================
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ==========================================
# HTML PAGE
# ==========================================
HTML = """
<!DOCTYPE html>
<html>

<head>
    <title>Raspberry Pi Rover</title>

    <style>

        body {
            background-color: #111;
            color: white;
            text-align: center;
            font-family: Arial;
        }

        h1 {
            margin-top: 20px;
        }

        img {
            border: 4px solid white;
            width: 640px;
            height: 480px;
        }

        .controls {
            margin-top: 20px;
        }

        button {
            width: 120px;
            height: 60px;
            margin: 10px;
            font-size: 20px;
            border-radius: 10px;
            border: none;
            cursor: pointer;
        }

        .stop {
            background-color: red;
            color: white;
        }

    </style>
</head>

<body>

    <h1>Raspberry Pi Rover</h1>

    <img src="/video_feed">

    <div class="controls">

        <div>
            <button onclick="sendCommand('forward')">Forward</button>
        </div>

        <div>
            <button onclick="sendCommand('left')">Left</button>

            <button class="stop" onclick="sendCommand('stop')">
                Stop
            </button>

            <button onclick="sendCommand('right')">Right</button>
        </div>

        <div>
            <button onclick="sendCommand('backward')">
                Backward
            </button>
        </div>

    </div>

    <script>

        function sendCommand(cmd) {
            fetch('/' + cmd);
        }

    </script>

</body>
</html>
"""

# ==========================================
# CAMERA STREAM FUNCTION
# ==========================================
def generate_frames():

    while True:

        success, frame = camera.read()

        if not success:
            break

        _, buffer = cv2.imencode('.jpg', frame)

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame +
            b'\r\n'
        )

# ==========================================
# WEB ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/forward')
def move_forward():
    forward()
    return "Forward"

@app.route('/backward')
def move_backward():
    backward()
    return "Backward"

@app.route('/left')
def move_left():
    left()
    return "Left"

@app.route('/right')
def move_right():
    right()
    return "Right"

@app.route('/stop')
def move_stop():
    stop()
    return "Stop"

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':

    print("===================================")
    print(" RASPBERRY PI ROVER WEB SERVER")
    print("===================================")
    print("Open this in your browser:")
    print("http://YOUR_PI_IP:5000")
    print("===================================")

    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            threaded=True
        )

    finally:
        stop()
        GPIO.cleanup()
        camera.release()
        cv2.destroyAllWindows()
        print("Shutdown complete")
