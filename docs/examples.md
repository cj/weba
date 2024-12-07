# Examples

## Basic Usage

Create a simple "Hello World" page:

```python
from weba import ui

with ui.div() as container:
    ui.h1("Hello, World!")
    ui.p("Welcome to weba!")

print(str(container))
```

This produces:

```html
<div>
    <h1>Hello, World!</h1>
    <p>Welcome to weba!</p>
</div>
```

## Working with Attributes

Add classes and other attributes to elements:

```python
with ui.div(class_=["container", "mx-auto", "p-4"]) as container:
    ui.h1("Styled Heading", class_="text-2xl font-bold")
    ui.p("Some content", class_="mt-2", data_testid="content")

print(str(container))
```

Output:

```html
<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">Styled Heading</h1>
    <p class="mt-2" data-testid="content">Some content</p>
</div>
```

## Nested Elements

Create complex nested structures:

```python
with ui.div(class_="card") as card:
    with ui.div(class_="card-header"):
        ui.h2("Card Title")
    with ui.div(class_="card-body"):
        ui.p("Card content goes here")
        with ui.ul(class_="list"):
            ui.li("Item 1")
            ui.li("Item 2")
    with ui.div(class_="card-footer"):
        ui.button("Click me!", class_="btn")
```

## Dynamic Content

Handle different types of values:

```python
from datetime import datetime

with ui.div() as content:
    ui.p(42)  # Numbers
    ui.p(3.14159)  # Floats
    ui.p(True)  # Booleans
    ui.p(datetime.now())  # DateTime objects
```

## HTMX Integration

Use HTMX attributes for dynamic behavior:

```python
with ui.form() as form:
    ui.input_(
        type="text",
        name="search",
        hx_post="/search",
        hx_trigger="keyup changed delay:500ms",
        hx_target="#results"
    )
    with ui.div(id="results"):
        ui.p("Results will appear here...")
```

## Class Manipulation

Dynamically modify classes:

```python
button = ui.button("Toggle")
button["class"].append("active")
button["class"].append("highlight")
print(str(button))  # <button class="active highlight">Toggle</button>
```

## Reusable Components

Create reusable UI components with flexible configurations:

```python
def create_card(
    title: str,
    content: str,
    items: list[str] | None = None,
    button_text: str | None = None,
    button_class: str = "btn"
) -> Tag:
    """Create a card component with customizable content."""
    with ui.div(class_="card") as card:
        with ui.div(class_="card-header"):
            ui.h2(title)

        with ui.div(class_="card-body"):
            ui.p(content)
            if items:
                with ui.ul(class_="list"):
                    for item in items:
                        ui.li(item)

        if button_text:
            with ui.div(class_="card-footer"):
                ui.button(button_text, class_=button_class)

    return card

# Usage examples:
# Full card with all features
card1 = create_card(
    title="Card Title",
    content="Card content goes here",
    items=["Item 1", "Item 2"],
    button_text="Click me!"
)

# Simple card without button
card2 = create_card(
    title="Simple Card",
    content="Just some content",
    items=["Only item"]
)

# Card without list items
card3 = create_card(
    title="No Items",
    content="A card without a list",
    button_text="Submit",
    button_class="btn-primary"
)
```
