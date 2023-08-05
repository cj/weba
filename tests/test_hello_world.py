from playwright.sync_api import Page, expect


def test_hello_world(page: Page):
    page.goto("https://playwright.dev/")

    expect(page).to_have_title("Fast and reliable end-to-end testing for modern web apps | Playwright")
