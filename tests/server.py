import os
import threading
import time
from typing import Optional

import uvicorn
from fastapi.responses import HTMLResponse
from playwright.sync_api import Page

from weba import uvicorn_server
from weba.app import load_app
from weba.document import get_document
from weba.utils import find_open_port


class Server:
    SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "screenshots")

    server_thread: Optional[threading.Thread]
    port: int
    base_url: str
    uvicorn_server: uvicorn.Server

    def __init__(self, page: Page) -> None:
        self.server_thread = None
        self.stop_server = False
        self.page = page
        self.doc = get_document()
        self.app = load_app()

    def start_server(self) -> None:
        """Start the webserver in a separate thread. This is the equivalent of `ui.run()` in a normal script."""
        self.port = find_open_port()
        self.base_url = f"http://localhost:{self.port}"

        app = self.app

        @app.get("/", response_class=HTMLResponse)
        async def index():
            return self.doc.render()

        self.server_thread = threading.Thread(
            target=self.run,
        )
        self.server_thread.start()

    def run(self):
        self.uvicorn_server = uvicorn_server(
            port=self.port,
            log_level="error",
            app=self.app,
        )
        self.uvicorn_server.run()

    def start(self, path: str = "/", timeout: float = 3.0) -> None:
        """Try to open the page until the server is ready or we time out.

        If the server is not yet running, start it.
        """
        if self.server_thread is None:
            self.start_server()

        deadline = time.time() + timeout

        while True:
            try:
                self.page.goto(f"http://localhost:{self.port}{path}")
                self.page.locator("//body")  # ensure page and JS are loaded

                break
            except Exception as e:
                if time.time() > deadline:
                    raise

                time.sleep(0.1)

                if self.server_thread and not self.server_thread.is_alive():
                    raise RuntimeError("The weba server has stopped running") from e

    def stop(self) -> None:
        """Stop the webserver."""

        if self.server_thread:
            self.uvicorn_server.should_exit = True
