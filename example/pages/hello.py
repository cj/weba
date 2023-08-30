from example.layouts import BaseLayout
from weba import ui


class HelloPage(BaseLayout):
    title = "Hello, Weba!"

    def content(self):
        ui.div("Hello, world!")
