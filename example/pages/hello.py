from weba import ui
from weba.base_page import BasePage


class HelloPage(BasePage):
    def content(self):
        ui.div("Hello, world!")
