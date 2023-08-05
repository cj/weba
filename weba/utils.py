import socket

from weba import settings


def find_open_port(port: int = settings.port, max_port: int = 65535):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while port <= max_port:
        try:
            sock.bind(("", port))
            sock.close()
            settings.port = port
            return port
        except OSError:
            port += 1
    raise IOError("no free ports")
