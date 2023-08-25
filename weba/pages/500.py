import traceback as tb

from weba import env, ui
from weba.base_page import BasePage


class InternalServerErrorPage(BasePage):
    def content(self):
        with ui.div(cls="container mx-auto"):
            with ui.div(cls="h-screen flex flex-col justify-center items-center align-middle"):
                with ui.div(cls="text-center"):
                    ui.h1("500", cls="m-0 font-bold text-8xl")
                    ui.h4("Internal Server Error", cls="m-0 text-2xl")
                if env.live_reload:
                    with ui.div(cls="mockup-code mt-10"):
                        [
                            ui.pre(ui.code(line), data_prefix=f"{i + 1}")
                            for i, line in enumerate(tb.format_exc().splitlines())
                        ]
