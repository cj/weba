import os
from multiprocessing import Process
from typing import Optional

import psutil

import weba


class Server:
    SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "screenshots")

    server_proc: Optional[Process]

    def __init__(self) -> None:
        self.server_proc = None
        self.stop_server = False

    def start_server(self) -> None:
        """Start the webserver in a separate thread. This is the equivalent of `ui.run()` in a normal script."""
        self.server_proc = Process(target=weba.run)
        self.server_proc.start()

    def start(self) -> None:
        """Try to open the page until the server is ready or we time out.

        If the server is not yet running, start it.
        """
        if self.server_proc is None:
            self.start_server()

    def stop(self) -> None:
        """Stop the webserver."""

        if self.server_proc:
            pid = self.server_proc.pid
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()

            self.server_proc.terminate()
