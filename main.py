import weba
from weba import Depends, Document, document, ui


@weba.get("/")
async def index(doc: Document = Depends(document)):
    with doc.body:
        ui.h1("Hello weba!")
    return doc.render()


weba.run()
