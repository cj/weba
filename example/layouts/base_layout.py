from contextlib import contextmanager
from typing import Any

from weba import Page, ui


class BaseLayout(Page):
    @contextmanager
    def layout(self) -> Any:
        with ui.div(cls="container mx-auto"):
            yield
