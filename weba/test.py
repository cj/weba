import os
import threading
import time
from collections.abc import Generator
from typing import Optional

import pytest
import uvicorn
from fastapi.responses import HTMLResponse
from playwright.sync_api import Page, expect

from weba import uvicorn_server
from weba.app import load_app
from weba.document import get_document
from weba.utils import find_open_port

expect = expect


class Weba:
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

    # on missing methods try calling self.app
    def __getattr__(self, name: str):
        return getattr(self.app, name)

    def start_server(self) -> None:
        """Start the webserver in a separate thread. This is the equivalent of `ui.run()` in a normal script."""
        self.port = find_open_port()
        self.base_url = f"http://localhost:{self.port}"

        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            return self.doc.render()

        self.server_thread = threading.Thread(
            target=self.run_server,
        )

        self.server_thread.start()

    def run_server(self):
        self.uvicorn_server = uvicorn_server(
            port=self.port,
            log_level="error",
            app=self.app,
        )
        self.uvicorn_server.run()

    def run(
        self,
        path: str = "/",
        timeout: float = 3.0,
    ) -> None:
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


@pytest.fixture(name="weba")
def weba_fixture(page: Page) -> Generator[Weba, None, None]:
    weba = Weba(page)
    yield weba
    weba.stop()
