import RPi.GPIO as GPIO
import time

# -------------------------
# Motor Pins (L298N)
# -------------------------
LEFT_IN1  = 17
LEFT_IN2  = 27
RIGHT_IN1 = 22
RIGHT_IN2 = 23

# -------------------------
# Ultrasonic Sensor Pins (HC-SR04)
# -------------------------
TRIG = 5
ECHO = 6

# -------------------------
# Configuration
# -------------------------
OBSTACLE_DISTANCE_CM = 20   # Stop threshold (cm)
SENSOR_TIMEOUT_S     = 0.04 # 40 ms (~6.8 m max range)
MIN_VALID_CM         = 2    # Below this = bad reading
MAX_VALID_CM         = 400  # Above this = bad reading
SAMPLES              = 3    # Readings to average per cycle

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
time.sleep(2)   # Let sensor settle

# -------------------------
# Motor Functions
# -------------------------
def move_forward():
    GPIO.output(LEFT_IN1,  GPIO.HIGH)
    GPIO.output(LEFT_IN2,  GPIO.LOW)
    GPIO.output(RIGHT_IN1, GPIO.HIGH)
    GPIO.output(RIGHT_IN2, GPIO.LOW)

def move_backward():
    GPIO.output(LEFT_IN1,  GPIO.LOW)
    GPIO.output(LEFT_IN2,  GPIO.HIGH)
    GPIO.output(RIGHT_IN1, GPIO.LOW)
    GPIO.output(RIGHT_IN2, GPIO.HIGH)

def turn_left():
    GPIO.output(LEFT_IN1,  GPIO.LOW)
    GPIO.output(LEFT_IN2,  GPIO.HIGH)
    GPIO.output(RIGHT_IN1, GPIO.HIGH)
    GPIO.output(RIGHT_IN2, GPIO.LOW)

def turn_right():
    GPIO.output(LEFT_IN1,  GPIO.HIGH)
    GPIO.output(LEFT_IN2,  GPIO.LOW)
    GPIO.output(RIGHT_IN1, GPIO.LOW)
    GPIO.output(RIGHT_IN2, GPIO.HIGH)

def stop():
    for pin in (LEFT_IN1, LEFT_IN2, RIGHT_IN1, RIGHT_IN2):
        GPIO.output(pin, GPIO.LOW)

# -------------------------
# Sensor Function
# -------------------------
def get_distance():
    """
    Returns distance in cm, or None if the reading is invalid/timed out.
    """
    # Send 10 µs trigger pulse
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    deadline = time.time() + SENSOR_TIMEOUT_S

    # Wait for echo to go HIGH
    pulse_start = time.time()
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > deadline:
            return None  # Sensor not responding

    # Wait for echo to go LOW
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > deadline:
            return None  # Echo held high too long

    distance = (pulse_end - pulse_start) * 17150
    distance = round(distance, 2)

    if not (MIN_VALID_CM < distance < MAX_VALID_CM):
        return None  # Out-of-range / noise

    return distance

def get_stable_distance():
    """
    Average multiple valid readings. Returns None if no valid sample.
    """
    readings = [get_distance() for _ in range(SAMPLES)]
    valid = [r for r in readings if r is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)

# -------------------------
# Obstacle Avoidance
# -------------------------
def avoid_obstacle():
    """
    Simple avoidance: reverse briefly, then turn right.
    """
    print("  -> Reversing...")
    move_backward()
    time.sleep(0.5)

    print("  -> Turning right...")
    turn_right()
    time.sleep(0.4)

    stop()

# -------------------------
# Main Loop
# -------------------------
print("Robot car started. Press Ctrl+C to stop.\n")

try:
    while True:
        distance = get_stable_distance()

        if distance is None:
            print("Sensor error — skipping cycle")
            time.sleep(0.1)
            continue

        print(f"Distance: {distance} cm")

        if distance > OBSTACLE_DISTANCE_CM:
            move_forward()
        else:
            stop()
            print("Obstacle detected!")
            avoid_obstacle()

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping robot.")

finally:
    stop()
    GPIO.cleanup()
    print("GPIO cleaned up. Bye!")