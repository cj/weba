from weba import doc, run, ui

doc["lang"] = "en"
doc.title = "Weba Example"

with doc.body:
    with ui.div(cls="container mx-auto prose"):
        ui.h1("Hello, world!")
        ui.p("This is an example of a weba app.")

run()
