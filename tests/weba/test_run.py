from weba import Depends, Document, document, ui
from weba.test import Weba, expect


def test_run_root(weba: Weba):
    @weba.get("/")
    async def index(doc: Document = Depends(document)):
        with doc.body:
            ui.h1("weba")
        return doc.render()

    weba.run()

    expect(weba.page.locator("//body")).to_contain_text("weba")


def test_run_root_two(weba: Weba):
    with weba.doc.body:
        ui.h1("weba 2")

    weba.run()

    expect(weba.page.locator("//body")).to_contain_text("weba 2")
