import RPi.GPIO as GPIO
import cv2
import threading
import sys
import tty
import termios
import time

# ==========================================
# MOTOR PINS (L298N)
# ==========================================
LEFT_IN1  = 17
LEFT_IN2  = 27
RIGHT_IN1 = 22
RIGHT_IN2 = 23

# ==========================================
# GLOBAL VARIABLES
# ==========================================
running = True
command = "STOP"

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
# KEYBOARD CONTROL THREAD
# ==========================================
def keyboard_control():

    global running
    global command

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        while running:

            key = sys.stdin.read(1)

            # FORWARD
            if key == 'w':
                command = "FORWARD"

            # BACKWARD
            elif key == 's':
                command = "BACKWARD"

            # LEFT
            elif key == 'a':
                command = "LEFT"

            # RIGHT
            elif key == 'd':
                command = "RIGHT"

            # STOP
            elif key == ' ':
                command = "STOP"

            # QUIT
            elif key.lower() == 'q':
                print("\nQ PRESSED -> SHUTTING DOWN")
                running = False
                break

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# ==========================================
# CAMERA THREAD
# ==========================================
def camera_loop():

    global running
    global command

    # USB CAMERA
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("ERROR: USB Camera not found")
        running = False
        return

    # OPTIONAL CAMERA SETTINGS
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while running:

        ret, frame = cap.read()

        if not ret:
            print("Camera frame error")
            break

        # TEXT OVERLAY
        cv2.putText(
            frame,
            f"COMMAND: {command}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # SHOW CAMERA
        cv2.imshow("Raspberry Pi Rover Camera", frame)

        # PRESS q INSIDE CAMERA WINDOW
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False
            break

    cap.release()
    cv2.destroyAllWindows()

# ==========================================
# START THREADS
# ==========================================
threading.Thread(target=keyboard_control, daemon=True).start()
threading.Thread(target=camera_loop, daemon=True).start()

# ==========================================
# MAIN CONTROL LOOP
# ==========================================
print("====================================")
print(" RASPBERRY PI ROVER CONTROL")
print("====================================")
print("W = Forward")
print("S = Backward")
print("A = Left")
print("D = Right")
print("SPACE = Stop")
print("Q = Quit")
print("====================================")

try:

    while running:

        if command == "FORWARD":
            forward()

        elif command == "BACKWARD":
            backward()

        elif command == "LEFT":
            left()

        elif command == "RIGHT":
            right()

        elif command == "STOP":
            stop()

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nKeyboard Interrupt")

finally:

    running = False

    stop()

    GPIO.cleanup()

    cv2.destroyAllWindows()

    print("GPIO cleanup complete.")
    print("Program exited safely.")
