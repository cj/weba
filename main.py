from weba import doc, run, ui

doc["lang"] = "en"
doc.title = "Weba Example"

with doc.body:
    ui.h1("Hello, world!")

run()
