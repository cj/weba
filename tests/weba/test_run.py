from fastapi import Depends
from playwright.sync_api import expect

from tests.server import Server
from weba import Document, document, ui


def test_run_root(server: Server):
    @server.app.get("/")
    async def index(doc: Document = Depends(document)):
        with doc.body:
            ui.h1("weba")
        return doc.render()

    server.start()

    expect(server.page.locator("//body")).to_contain_text("weba")


def test_run_root_two(server: Server):
    with server.doc.body:
        ui.h1("weba 2")

    server.start()

    expect(server.page.locator("//body")).to_contain_text("weba 2")
