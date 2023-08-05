from playwright.sync_api import Page, expect

import weba

base_url = f"http://localhost:{weba.settings.port}/"


def test_run(page: Page):
    page.goto(base_url)

    expect(page.locator("//body")).to_contain_text("weba")
