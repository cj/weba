from fastapi import Depends

from weba import WebaDocument, app, document, run, ui


@app.get("/")
async def index(doc: WebaDocument = Depends(document)):
    with doc.body:
        ui.h1("Hello weba!")
    return doc.render()


run()
