# Examples

## Basic Usage

Create a simple "Hello World" page:

```python
from weba import ui

with ui.div() as container:
    ui.h1("Hello, World!")
    ui.p("Welcome to weba!")

print(container)
```

Output:

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

print(container)
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

print(card)
```

Output:

```html
<div class="card">
    <div class="card-header">
        <h2>Card Title</h2>
    </div>
    <div class="card-body">
        <p>Card content goes here</p>
        <ul class="list">
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </div>
    <div class="card-footer">
        <button class="btn">Click me!</button>
    </div>
</div>
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

print(content)
```

Output:

```html
<div>
    <p>42</p>
    <p>3.14159</p>
    <p>True</p>
    <p>2024-02-20 10:30:45</p>
</div>
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

print(form)
```

Output:

```html
<form>
    <input type="text" name="search" hx-post="/search" hx-trigger="keyup changed delay:500ms" hx-target="#results" />
    <div id="results">
        <p>Results will appear here...</p>
    </div>
</form>
```

## Class Manipulation

Dynamically modify classes:

```python
button = ui.button("Toggle")
button["class"].append("active")
button["class"].append("highlight")
print(button)
```

Output:

```html
<button class="active highlight">Toggle</button>
```

## Tag Manipulation

Extract, replace and modify tags:

```python
# Extract a tag from its parent
with ui.div() as container:
    child = ui.p("Test")
    extracted = child.extract()  # Removes from parent but keeps the tag
    print(extracted.parent)  # None
    print(container)
```

Output:

```html
<div></div>
```

```python
# Replace tags
with ui.div() as container:
    original = ui.p("Original")
    ui.span("Other")

    # Replace with a single tag
    original.replace_with(ui.h2("New"))
    print(container)
```

Output:

```html
<div>
    <h2>New</h2>
    <span>Other</span>
</div>
```

```python
# Replace with multiple tags
with ui.div() as container:
    original = ui.p("Original")
    original.replace_with(
        ui.h2("First"),
        ui.h3("Second")
    )
    print(container)
```

Output:

```html
<div>
    <h2>First</h2>
    <h3>Second</h3>
</div>
```

```python
# Set tag attributes directly
button = ui.button("Click me")
button.string = "Submit"  # Change content
button.name = "input"    # Change tag type
button.attrs["class"] = ["primary", "large"]  # Set multiple classes
button.attrs["data-test"] = "value"  # Set custom attribute

print(button)
```

Output:

```html
<input
    class="primary large"
    data-test="value"
>Submit</input>
```

## Raw HTML Integration

Parse and integrate raw HTML strings:

```python
# Basic raw HTML
tag = ui.raw("<div>Hello World</div>")
tag["class"].append("raw")
print(tag)  # <div class="raw">Hello World</div>

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
print(text)  # Hello World

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

print(container)  # <div>First <strong>important</strong> last</div>

# Complex text layout

with ui.article() as article:
    ui.text("Start of article. ")
    with ui.em():
        ui.text("Emphasized text. ")
    ui.text("Regular text. ")
    with ui.strong():
        ui.text("Strong text.")
    ui.text(" End of article.")

print(article)
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
    print(div)  # <div data-user='{"name": "John", "age": 30}'></div>

# Array attributes
items = ["apple", "banana", "orange"]
with ui.div(data_items=items) as div:
    print(div)  # <div data-items='["apple", "banana", "orange"]'></div>

# Nested structures
complex_data = {
    "user": {"name": "John", "age": 30},
    "items": ["apple", "banana"],
    "active": True
}
with ui.div(data_complex=complex_data) as div:
    print(div)
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
print(button)  # <button>Submit</button>

# Find all cards after .card comments
cards = container.comment(".card")
for card in cards:
    print(card)
# <div class="card">Card 1</div>
# <div class="card">Card 2</div>

# No match returns None for comment_one
no_match = container.comment_one("#nonexistent")
print(no_match)  # None

# No match returns empty list for comment
no_matches = container.comment("#nonexistent")
print(no_matches)  # []
```
