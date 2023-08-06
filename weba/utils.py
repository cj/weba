import socket

from .env import env


def find_open_port(port: int = env.port, max_port: int = 65535):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while port <= max_port:
        location = (env.host, port)
        check = sock.connect_ex(location)

        if check != 0:
            return port

        port += 1

    raise IOError("no free ports")
