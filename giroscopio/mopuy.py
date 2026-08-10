from mpu6050 import mpu6050
from vpython import *
import time
import math


# ----------------------------
# MPU6050 setup
# ----------------------------

sensor = mpu6050(0x68)


# ----------------------------
# VPython setup
# ----------------------------

scene.title = "MPU6050 3D Orientation"
scene.width = 1000
scene.height = 700
scene.background = color.white

scene.center = vector(0, 0, 0)
scene.range = 4


# World axes

arrow(pos=vector(0,0,0),
      axis=vector(3,0,0),
      color=color.red,
      shaftwidth=0.03)

arrow(pos=vector(0,0,0),
      axis=vector(0,3,0),
      color=color.green,
      shaftwidth=0.03)

arrow(pos=vector(0,0,0),
      axis=vector(0,0,3),
      color=color.blue,
      shaftwidth=0.03)


label(pos=vector(3.2,0,0), text="X")
label(pos=vector(0,3.2,0), text="Y")
label(pos=vector(0,0,3.2), text="Z")


# ----------------------------
# Create MPU6050 model
# ----------------------------

body = box(
    pos=vector(0,0,0),
    length=2,
    width=1,
    height=0.3,
    color=color.orange
)

# Arrow showing sensor front direction

front_arrow = arrow(
    pos=vector(0,0,0),
    axis=vector(1.5,0,0),
    color=color.red,
    shaftwidth=0.08
)


# ----------------------------
# Orientation variables
# ----------------------------

roll = 0.0
pitch = 0.0
yaw = 0.0

dt = 0.01       # 100Hz

alpha = 0.96    # complementary filter


last_time = time.time()


# ----------------------------
# Main loop
# ----------------------------

while True:

    rate(100)

    try:

        now = time.time()
        dt = now - last_time
        last_time = now


        # ------------------------
        # Read sensor
        # ------------------------

        accel = sensor.get_accel_data()
        gyro = sensor.get_gyro_data()


        ax = accel["x"]
        ay = accel["y"]
        az = accel["z"]


        gx = gyro["x"]
        gy = gyro["y"]
        gz = gyro["z"]


        # ------------------------
        # Accelerometer angles
        # ------------------------

        accel_roll = math.atan2(
            ay,
            math.sqrt(ax*ax + az*az)
        )

        accel_pitch = math.atan2(
            -ax,
            math.sqrt(ay*ay + az*az)
        )


        # ------------------------
        # Gyroscope integration
        # ------------------------

        roll += math.radians(gx) * dt
        pitch += math.radians(gy) * dt
        yaw += math.radians(gz) * dt


        # ------------------------
        # Complementary filter
        # ------------------------

        roll = alpha * roll + (1-alpha) * accel_roll
        pitch = alpha * pitch + (1-alpha) * accel_pitch


        # ------------------------
        # Convert to VPython
        # ------------------------

        # Reset orientation
        body.axis = vector(
            math.cos(pitch),
            math.sin(roll),
            math.sin(pitch)
        )

        body.up = vector(
            0,
            math.cos(roll),
            -math.sin(roll)
        )


        front_arrow.pos = body.pos
        front_arrow.axis = body.axis * 1.5


        print(
            "Roll:",
            math.degrees(roll),
            "Pitch:",
            math.degrees(pitch),
            "Yaw:",
            math.degrees(yaw)
        )


    except OSError:

        print("MPU6050 disconnected - keeping last orientation")


    time.sleep(0.01)