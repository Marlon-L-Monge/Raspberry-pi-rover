import RPi.GPIO as GPIO
from time import sleep, time

# ==========================================
# GPIO PIN SETUP
# ==========================================

# L298N Motor Driver Pins
MOTOR_LEFT_FORWARD   = 17
MOTOR_LEFT_BACKWARD  = 27
MOTOR_RIGHT_FORWARD  = 22
MOTOR_RIGHT_BACKWARD = 23

# HC-SR04 Ultrasonic Sensor Pins
ULTRASONIC_TRIGGER = 5
ULTRASONIC_ECHO    = 6

# ==========================================
# SETTINGS
# ==========================================

STOP_DISTANCE = 20          # cm
SENSOR_TIMEOUT = 0.04       # seconds
READING_COUNT = 3

MIN_DISTANCE = 2
MAX_DISTANCE = 400

# ==========================================
# GPIO INITIALIZATION
# ==========================================

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

motor_pins = [
    MOTOR_LEFT_FORWARD,
    MOTOR_LEFT_BACKWARD,
    MOTOR_RIGHT_FORWARD,
    MOTOR_RIGHT_BACKWARD
]

for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

GPIO.setup(ULTRASONIC_TRIGGER, GPIO.OUT)
GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)

GPIO.output(ULTRASONIC_TRIGGER, False)

print("Initializing sensor...")
sleep(2)

# ==========================================
# MOTOR CONTROL FUNCTIONS
# ==========================================

def drive_forward():
    GPIO.output(MOTOR_LEFT_FORWARD, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_BACKWARD, GPIO.LOW)

    GPIO.output(MOTOR_RIGHT_FORWARD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.LOW)

def drive_backward():
    GPIO.output(MOTOR_LEFT_FORWARD, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_BACKWARD, GPIO.HIGH)

    GPIO.output(MOTOR_RIGHT_FORWARD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.HIGH)

def rotate_left():
    GPIO.output(MOTOR_LEFT_FORWARD, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_BACKWARD, GPIO.HIGH)

    GPIO.output(MOTOR_RIGHT_FORWARD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.LOW)

def rotate_right():
    GPIO.output(MOTOR_LEFT_FORWARD, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_BACKWARD, GPIO.LOW)

    GPIO.output(MOTOR_RIGHT_FORWARD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.HIGH)

def halt():
    for pin in motor_pins:
        GPIO.output(pin, GPIO.LOW)

# ==========================================
# DISTANCE SENSOR FUNCTIONS
# ==========================================

def measure_distance():
    """
    Measure distance using HC-SR04.
    Returns:
        float distance in cm
        OR None if invalid
    """

    # Trigger pulse
    GPIO.output(ULTRASONIC_TRIGGER, True)
    sleep(0.00001)
    GPIO.output(ULTRASONIC_TRIGGER, False)

    timeout_limit = time() + SENSOR_TIMEOUT

    # Wait for echo HIGH
    while GPIO.input(ULTRASONIC_ECHO) == 0:
        pulse_start = time()

        if pulse_start > timeout_limit:
            return None

    # Wait for echo LOW
    while GPIO.input(ULTRASONIC_ECHO) == 1:
        pulse_end = time()

        if pulse_end > timeout_limit:
            return None

    pulse_duration = pulse_end - pulse_start

    distance_cm = pulse_duration * 17150
    distance_cm = round(distance_cm, 2)

    if distance_cm < MIN_DISTANCE or distance_cm > MAX_DISTANCE:
        return None

    return distance_cm

def get_average_distance():
    """
    Take several readings and average them.
    """

    collected = []

    for _ in range(READING_COUNT):
        result = measure_distance()

        if result is not None:
            collected.append(result)

    if len(collected) == 0:
        return None

    average = sum(collected) / len(collected)

    return round(average, 2)

# ==========================================
# OBSTACLE AVOIDANCE
# ==========================================

def evade_obstacle():

    print("Obstacle detected!")

    print("Backing up...")
    drive_backward()
    sleep(0.5)

    print("Turning...")
    rotate_right()
    sleep(0.4)

    halt()

# ==========================================
# MAIN PROGRAM LOOP
# ==========================================

print("Robot running...")
print("Press CTRL + C to stop.\n")

try:

    while True:

        current_distance = get_average_distance()

        if current_distance is None:
            print("Invalid sensor reading")
            sleep(0.1)
            continue

        print(f"Distance = {current_distance} cm")

        if current_distance > STOP_DISTANCE:
            drive_forward()

        else:
            halt()
            evade_obstacle()

        sleep(0.1)

except KeyboardInterrupt:

    print("\nProgram stopped by user.")

finally:

    halt()
    GPIO.cleanup()

    print("GPIO cleanup complete.")
