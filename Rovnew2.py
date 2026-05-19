import RPi.GPIO as GPIO
import time
import threading
import sys
import termios
import tty

# =========================
# MOTOR PINS (L298N)
# =========================
LEFT_IN1  = 17
LEFT_IN2  = 27
RIGHT_IN1 = 22
RIGHT_IN2 = 23

# =========================
# ULTRASONIC SENSOR
# =========================
TRIG = 5
ECHO = 6

# =========================
# SETTINGS
# =========================
OBSTACLE_DISTANCE_CM = 20
TIMEOUT = 0.04

MIN_CM = 2
MAX_CM = 400
SAMPLES = 3

# =========================
# GLOBAL STOP FLAG
# =========================
running = True

# =========================
# GPIO SETUP
# =========================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

motor_pins = [LEFT_IN1, LEFT_IN2, RIGHT_IN1, RIGHT_IN2]

for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)
time.sleep(2)

# =========================
# MOTOR FUNCTIONS
# =========================
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

def stop():
    for pin in motor_pins:
        GPIO.output(pin, GPIO.LOW)

# =========================
# DISTANCE SENSOR
# =========================
def measure_distance():

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    timeout = time.time() + TIMEOUT

    pulse_start = None
    pulse_end = None

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None

    if pulse_start is None or pulse_end is None:
        return None

    duration = pulse_end - pulse_start
    distance = duration * 17150

    if distance < MIN_CM or distance > MAX_CM:
        return None

    return distance

def get_distance():

    values = []

    for _ in range(SAMPLES):
        d = measure_distance()
        if d is not None:
            values.append(d)

    if not values:
        return None

    return sum(values) / len(values)

# =========================
# KEY LISTENER (Q = STOP)
# =========================
def key_listener():
    global running

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        while running:
            key = sys.stdin.read(1)

            if key.lower() == 'q':
                print("\nQ pressed — stopping robot")
                running = False
                stop()
                break

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# =========================
# OBSTACLE AVOIDANCE
# =========================
def avoid():
    backward()
    time.sleep(0.5)

    right()
    time.sleep(0.4)

    stop()

# =========================
# START KEY THREAD
# =========================
threading.Thread(target=key_listener, daemon=True).start()

# =========================
# MAIN LOOP
# =========================
print("Robot started (press Q to stop)")

try:
    while running:

        dist = get_distance()

        if dist is None:
            time.sleep(0.1)
            continue

        print("Distance:", round(dist, 2), "cm")

        if dist > OBSTACLE_DISTANCE_CM:
            forward()
        else:
            stop()
            avoid()

        time.sleep(0.1)

finally:
    running = False
    stop()
    GPIO.cleanup()
    print("GPIO cleaned safely. Robot off.")
