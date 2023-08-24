from weba import app, doc, run, ui

doc["lang"] = "en"
doc.title = "Weba Example"


@app.post("/handle_click")
def handle_click():
    return ui.p("Clicked!")


with doc.body:
    with ui.div(cls="container mx-auto prose"):
        ui.h1("Hello, world!")

        ui.p("Not Clicked")

        ui.button(
            "Click me!",
            cls="btn btn-primary",
            hx_post="/handle_click",
            hx_target="previous p",
            hx_swap="outerHTML",
        )

run()
