from contextlib import contextmanager

from weba import Page, ui
from weba.components import browser_component


@contextmanager
def container():
    with ui.div(cls="container mx-auto prose h-screen flex justify-center items-center text-center"):
        yield


class NotFoundPage(Page):
    def content(self):
        url = self.request.url._url  # type: ignore

        with container():
            with browser_component(url):
                with ui.div(cls="py-10"):
                    ui.h1("404", cls="mb-5")
                    ui.p("Page Not Found", cls="uppercase")
