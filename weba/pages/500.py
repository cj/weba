import traceback as tb

from weba import Page, env, ui


class InternalServerErrorPage(Page):
    def content(self):
        with ui.div(cls="container mx-auto py-20 h-screen flex flex-col"):
            with ui.div(cls="h-full flex flex-col justify-center items-center align-middle"):
                with ui.div(cls="text-center"):
                    ui.h1("500", cls="m-0 font-bold text-8xl")
                    ui.h4("Internal Server Error", cls="m-0 text-2xl")
                if env.live_reload:
                    with ui.div(
                        cls="mockup-code mt-10 pb-0 border border-gray-700 bg-gray-700 dark:bg-base-300 shadow-xl"
                    ):
                        with ui.div(cls="flex flex-col h-full overflow-auto pb-8 -mb-5"):
                            [
                                ui.pre(ui.code(line), data_prefix=f"{i + 1}")
                                for i, line in enumerate(tb.format_exc().splitlines())
                            ]
