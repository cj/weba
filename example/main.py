from weba import Depends, WebaDocument, app, doc, run, ui, weba_document

doc["lang"] = "en"
doc.title = "Weba Example"

state = {"clicked": 0}


def clicked_component():
    if state["clicked"] == 0:
        return ui.p("Not Clicked")

    return ui.p(f"Clicked {state['clicked']}!")


@app.post("/handle_click")
def handle_click():
    state["clicked"] += 1

    return clicked_component()


@app.get("/")
def index(doc: WebaDocument = Depends(weba_document)):
    with doc.body:
        with ui.div(cls="container mx-auto prose"):
            ui.h1("Hello, world!")

            clicked_component()

            ui.button(
                "Click me!",
                cls="btn btn-primary",
                hx_post="/handle_click",
                hx_target="previous p",
                hx_swap="outerHTML",
            )

    return doc


run()
