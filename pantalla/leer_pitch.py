import socket
import msgpack
import time


SOCKET_PATH = "/var/run/arduino-router.sock"


def get_pitch():

    request = [
        0,              # RPC Request
        1,              # Message ID
        "get_pitch",    # Funcion del STM32
        []              # Sin parametros
    ]

    packed_request = msgpack.packb(request)

    with socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM
    ) as client:

        client.settimeout(1.0)

        client.connect(SOCKET_PATH)

        client.sendall(packed_request)

        data = client.recv(1024)

        response = msgpack.unpackb(
            data,
            raw=False
        )

    # Formato:
    # [1, msgid, error, result]

    error = response[2]
    result = response[3]

    if error is not None:
        raise RuntimeError(
            f"Error Bridge: {error}"
        )

    return float(result)


while True:

    try:

        pitch = get_pitch()

        print(
            f"Pitch desde STM32: {pitch:.2f} grados"
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

    time.sleep(0.5)