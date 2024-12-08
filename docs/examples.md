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

## Raw HTML Integration

Parse and integrate raw HTML strings:

```python
# Basic raw HTML
tag = ui.raw("<div>Hello World</div>")
tag["class"].append("raw")
print(str(tag))  # <div class="raw">Hello World</div>

# Complex nested HTML
html = """
<article class="post">
    <h2>Blog Post</h2>
    <div class="content">
        <p>First paragraph</p>
        <p>Second paragraph</p>
    </div>
</article>
"""
content = ui.raw(html)

# Use raw HTML within context managers
with ui.div(class_="wrapper") as container:
    ui.raw("<header>Page Title</header>")
    with ui.main():
        ui.raw("<p>Some content</p>")
    ui.raw("<footer>Page Footer</footer>")
```

## Text Node Handling

Create and manipulate text nodes:

```python
# Basic text nodes
text = ui.text("Hello World")
print(str(text))  # Hello World

# Different content types
ui.text(42)  # "42"
ui.text(3.14)  # "3.14"
ui.text(True)  # "True"
ui.text(None)  # "None"

# Text nodes in context
with ui.div() as container:
    ui.text("First ")
    with ui.strong():
        ui.text("important")
    ui.text(" last")

print(str(container))  # <div>First <strong>important</strong> last</div>

# Complex text layout

with ui.article() as article:
    ui.text("Start of article. ")
    with ui.em():
        ui.text("Emphasized text. ")
    ui.text("Regular text. ")
    with ui.strong():
        ui.text("Strong text.")
    ui.text(" End of article.")

print(str(article))
# <article>Start of article. <em>Emphasized text. </em>Regular text. <strong>Strong text.</strong> 
# End of article.</article>
```

## JSON Attributes

Handle complex data structures as HTML attributes:

```python
import json

# Dictionary attributes
data = {"name": "John", "age": 30}
with ui.div(data_user=data) as div:
    print(str(div))  # <div data-user='{"name": "John", "age": 30}'></div>

# Array attributes
items = ["apple", "banana", "orange"]
with ui.div(data_items=items) as div:
    print(str(div))  # <div data-items='["apple", "banana", "orange"]'></div>

# Nested structures
complex_data = {
    "user": {"name": "John", "age": 30},
    "items": ["apple", "banana"],
    "active": True
}
with ui.div(data_complex=complex_data) as div:
    print(str(div))
    # <div data-complex='{"user": {"name": "John", "age": 30}, "items": ["apple", "banana"], "active": true}'></div>

    # Access and parse the JSON data
    stored_data = json.loads(div["data-complex"])
    print(stored_data["user"]["name"])  # John
    print(stored_data["items"][0])      # apple
    print(stored_data["active"])        # True
```

## Comment Selectors

Find elements that follow HTML comments:

```python
# HTML with comments
html = """
<div>
    <!-- #submit-button -->
    <button>Submit</button>
    
    <!-- .card -->
    <div class="card">Card 1</div>
    <!-- .card -->
    <div class="card">Card 2</div>
</div>
"""

container = ui.raw(html)

# Find first button after #submit-button comment
button = container.comment_one("#submit-button")
print(str(button))  # <button>Submit</button>

# Find all cards after .card comments
cards = container.comment(".card")
for card in cards:
    print(str(card))
# <div class="card">Card 1</div>
# <div class="card">Card 2</div>

# No match returns None for comment_one
no_match = container.comment_one("#nonexistent")
print(no_match)  # None

# No match returns empty list for comment
no_matches = container.comment("#nonexistent") 
print(no_matches)  # []
```
