from contextlib import contextmanager
from typing import Any

from weba import ui
from weba.utils import merge_class


@contextmanager
def browser_component(url: str, **kwargs: Any):
    with ui.div(cls=merge_class("mockup-browser border border-gray-700 bg-base-300 shadow-xl", kwargs), **kwargs):
        with ui.div(cls="mockup-browser-toolbar"):
            ui.div(url, cls="input")

        yield
