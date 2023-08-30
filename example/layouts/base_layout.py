from contextlib import contextmanager
from typing import Any

from weba import BasePage, ui


class BaseLayout(BasePage):
    @contextmanager
    def layout(self) -> Any:
        with ui.div(cls="container mx-auto"):
            yield
