from flask import Flask, render_template
import psutil
import socket
import time
import os

app = Flask(__name__)

# =========================
# GPIO STATE (NO FAKE DATA)
# =========================
GPIO_STATE = {
    "17": 0,
    "27": 0,
    "22": 0,
    "23": 0
}

LAST_COMMAND = "STOP"
ERROR_LOG = []

# =========================
# SYSTEM INFO FUNCTIONS
# =========================
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "N/A"

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read()) / 1000, 1)
    except:
        return None

def get_uptime():
    return int(time.time() - psutil.boot_time())

# =========================
# MOTOR STATE LOGIC (BASED ON GPIO)
# =========================
def decode_motor_state():
    l_fwd = GPIO_STATE["17"]
    l_back = GPIO_STATE["27"]
    r_fwd = GPIO_STATE["22"]
    r_back = GPIO_STATE["23"]

    if l_fwd and r_fwd:
        return "FORWARD"
    elif l_back and r_back:
        return "BACKWARD"
    elif l_back and r_fwd:
        return "LEFT"
    elif l_fwd and r_back:
        return "RIGHT"
    else:
        return "STOP"

# =========================
# DASHBOARD ROUTE
# =========================
@app.route("/")
def dashboard():

    data = {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "temp": get_cpu_temp(),
        "ip": get_ip(),
        "uptime": get_uptime(),
        "motor_state": decode_motor_state(),
        "last_command": LAST_COMMAND,
        "gpio": GPIO_STATE,
        "errors": ERROR_LOG[-5:]
    }

    return render_template("index.html", data=data)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
