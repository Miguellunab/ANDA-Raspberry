#!/usr/bin/env python3
"""Diagnostico de orientacion relativa para un sensor MPU6050.

Al iniciar, el sensor debe permanecer quieto y en la postura que se desea
considerar como cero. El programa calibra el offset del giroscopio y despues
muestra las lecturas de los tres ejes y los angulos relativos suavizados.
"""

import math
import time

from mpu6050 import mpu6050


I2C_ADDRESS = 0x68
SAMPLE_HZ = 100.0
OUTPUT_HZ = 10.0
CALIBRATION_SECONDS = 3.0
RECONNECT_TIMEOUT_SECONDS = 1.0
RECONNECT_RETRY_SECONDS = 0.05

# El giroscopio domina a corto plazo y el acelerometro corrige la deriva de
# roll y pitch lentamente. Un valor mayor suaviza mas, pero responde mas lento.
COMPLEMENTARY_ALPHA = 0.98

# Segundo suavizado para que la salida mostrada sea mas estable.
OUTPUT_SMOOTHING_ALPHA = 0.20

# Ignora velocidades angulares residuales despues de calibrar. Esto reduce la
# deriva cuando el sensor esta quieto. La unidad es grados por segundo.
GYRO_DEADBAND_DPS = 0.15

# Evita que la cifra visible tiemble por cambios extremadamente pequenos.
ANGLE_DEADBAND_DEG = 0.10


def accelerometer_angles(accel):
    """Devuelve roll y pitch, en grados, calculados usando la gravedad."""
    ax = accel["x"]
    ay = accel["y"]
    az = accel["z"]

    roll = math.degrees(math.atan2(ay, math.sqrt(ax * ax + az * az)))
    pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
    return roll, pitch


def calibrate_gyroscope(sensor):
    """Calcula el offset medio de cada eje con el sensor inmovil."""
    sample_count = max(1, int(CALIBRATION_SECONDS * SAMPLE_HZ))
    totals = {"x": 0.0, "y": 0.0, "z": 0.0}

    print(
        f"Mantenga la cabeza recta y el sensor completamente quieto "
        f"durante {CALIBRATION_SECONDS:.0f} segundos..."
    )

    next_sample = time.monotonic()
    for _ in range(sample_count):
        gyro = sensor.get_gyro_data()
        for axis in totals:
            totals[axis] += gyro[axis]

        next_sample += 1.0 / SAMPLE_HZ
        time.sleep(max(0.0, next_sample - time.monotonic()))

    offsets = {axis: totals[axis] / sample_count for axis in totals}
    print(
        "Calibracion terminada. Offset del giroscopio (grados/s): "
        f"X={offsets['x']:+.3f}, Y={offsets['y']:+.3f}, "
        f"Z={offsets['z']:+.3f}"
    )
    return offsets


def remove_deadband(value, threshold):
    """Devuelve cero cuando el valor esta dentro de una zona muerta."""
    return 0.0 if abs(value) < threshold else value


def smooth(previous, current):
    """Filtro exponencial para los valores mostrados."""
    return (
        previous * (1.0 - OUTPUT_SMOOTHING_ALPHA)
        + current * OUTPUT_SMOOTHING_ALPHA
    )


def read_sensor_with_recovery(sensor, last_pitch):
    """Lee el sensor y permite cortes breves sin perder el ultimo angulo."""
    try:
        return sensor.get_accel_data(), sensor.get_gyro_data()
    except OSError:
        deadline = time.monotonic() + RECONNECT_TIMEOUT_SECONDS
        print(
            f"Conexion interrumpida; manteniendo pitch={last_pitch:+.2f} "
            "grados mientras se recupera..."
        )

        while time.monotonic() < deadline:
            time.sleep(RECONNECT_RETRY_SECONDS)
            try:
                accel = sensor.get_accel_data()
                gyro = sensor.get_gyro_data()
                print("Conexion recuperada.")
                return accel, gyro
            except OSError:
                continue

        raise OSError(
            f"el MPU6050 no respondio durante {RECONNECT_TIMEOUT_SECONDS:.1f} s"
        )


def main():
    sensor = mpu6050(I2C_ADDRESS)
    gyro_offset = calibrate_gyroscope(sensor)

    # La inclinacion que tenga el sensor en este instante pasa a ser la postura
    # neutral. Roll y pitch son absolutos respecto a la gravedad antes de restar
    # esta referencia. Yaw empieza arbitrariamente en cero.
    initial_accel = sensor.get_accel_data()
    neutral_roll, neutral_pitch = accelerometer_angles(initial_accel)

    roll = neutral_roll
    pitch = neutral_pitch
    yaw = 0.0
    display_roll = 0.0
    display_pitch = 0.0
    display_yaw = 0.0

    print(
        "Posicion neutral establecida como 0 grados. "
        "Mueva la cabeza lentamente para identificar los ejes."
    )
    print("Detenga el programa con Ctrl+C.\n")

    sample_period = 1.0 / SAMPLE_HZ
    output_period = 1.0 / OUTPUT_HZ
    previous_time = time.monotonic()
    next_sample = previous_time
    next_output = previous_time

    try:
        while True:
            now = time.monotonic()
            dt = now - previous_time
            previous_time = now

            accel, raw_gyro = read_sensor_with_recovery(sensor, display_pitch)

            # No se integra el tiempo que el sensor estuvo desconectado. De lo
            # contrario, la primera lectura recuperada produciria un salto.
            recovered_at = time.monotonic()
            if recovered_at - now >= RECONNECT_RETRY_SECONDS:
                previous_time = recovered_at
                next_sample = recovered_at
                next_output = recovered_at
                continue

            accel_roll, accel_pitch = accelerometer_angles(accel)

            gyro = {
                axis: remove_deadband(
                    raw_gyro[axis] - gyro_offset[axis], GYRO_DEADBAND_DPS
                )
                for axis in ("x", "y", "z")
            }

            roll = (
                COMPLEMENTARY_ALPHA * (roll + gyro["x"] * dt)
                + (1.0 - COMPLEMENTARY_ALPHA) * accel_roll
            )
            pitch = (
                COMPLEMENTARY_ALPHA * (pitch + gyro["y"] * dt)
                + (1.0 - COMPLEMENTARY_ALPHA) * accel_pitch
            )
            yaw += gyro["z"] * dt

            relative_roll = roll - neutral_roll
            relative_pitch = pitch - neutral_pitch

            display_roll = smooth(display_roll, relative_roll)
            display_pitch = smooth(display_pitch, relative_pitch)
            display_yaw = smooth(display_yaw, yaw)

            display_roll = remove_deadband(display_roll, ANGLE_DEADBAND_DEG)
            display_pitch = remove_deadband(display_pitch, ANGLE_DEADBAND_DEG)
            display_yaw = remove_deadband(display_yaw, ANGLE_DEADBAND_DEG)

            if now >= next_output:
                print(
                    f"Inclinacion pitch={display_pitch:+7.2f} grados"
                )
                next_output = now + output_period

            next_sample += sample_period
            time.sleep(max(0.0, next_sample - time.monotonic()))

    except KeyboardInterrupt:
        print("\nPrograma detenido.")
    except OSError as error:
        print(f"\nNo se pudo leer el MPU6050: {error}")
        print("Revise la conexion, la alimentacion y que I2C este habilitado.")


if __name__ == "__main__":
    main()
