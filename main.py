from fastapi import Depends

from weba import Document, app, document, run, ui


@app.get("/")
async def index(doc: Document = Depends(document)):
    with doc.body:
        ui.h1("Hello weba!")
    return doc.render()


run()
