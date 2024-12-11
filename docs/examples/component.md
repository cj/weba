# Component Examples

## Basic Component

Create a simple button component:

```python
from weba import Component, ui

class Button(Component):
    html = "<button>Example</button>"

    def __init__(self, msg: str):
        self.msg = msg

    def render(self):
        self.string = self.msg

# Usage
with ui.div() as container:
    Button("Click me")

print(str(container))  # <div><button>Click me</button></div>
```

## Using Tag Decorators

Components with tag decorators for more control:

```python
class Button(Component):
    html = "<div><button class='btn'>Example</button></div>"

    def __init__(self, msg: str):
        self.msg = msg

    @tag("button")
    def button_tag(self, t: Tag):
        t.string = self.msg

# Usage
with ui.div() as container:
    Button("Submit")

print(str(container))  # <div><div><button class="btn">Submit</button></div></div>
```

## Comment Selectors

Use HTML comments as selectors:

```python
class Button(Component):
    html = """<div><!-- #button --><button>Example</button></div>"""

    def __init__(self, msg: str):
        self.msg = msg

    @tag("<!-- #button -->")
    def button_tag(self, t: Tag):
        t.string = self.msg

# Usage
with ui.div() as container:
    Button("Delete")

print(str(container))  # <div><div><!-- #button --><button>Delete</button></div></div>
```

## Async Components

Create components with async rendering:

```python
import asyncio

class AsyncButton(Component):
    html = "<button></button>"

    def __init__(self, msg: str):
        self.msg = msg

    async def render(self):
        await asyncio.sleep(0.01)  # Simulate async operation
        self.string = self.msg

# Usage
async def main():
    with ui.div() as container:
        await AsyncButton("Async Click Me")
        await AsyncButton("Another Button")
    
    print(str(container))
    # <div><button>Async Click Me</button><button>Another Button</button></div>
```

## Component with Layout

Create a layout component with header, main, and footer sections:

```python
from bs4 import Doctype

class Layout(Component):
    html = """
    <!DOCTYPE html>
    <html>
        <header></header>
        <main></main>
        <footer></footer>
    </html>
    """

    def render(self):
        self.insert(0, Doctype("HTML"))

    @tag("header")
    def header(self):
        pass

    @tag("main")
    def main(self):
        pass

    @tag("footer")
    def footer(self):
        pass

# Usage
layout = Layout()

with layout as html:
    with html.header:
        ui.nav("navbar")

    with html.main:
        ui.h1("Hello, World!")

    with html.footer:
        ui.span("contact us")

print(str(html))
# Output will include DOCTYPE and all sections with content
```

## Extract and Clear Tags

Manipulate component structure with extract and clear options:

```python
class Button(Component):
    html = "<div><button class='btn'>Example</button></div>"

    def __init__(self, msg: str):
        self.msg = msg

    @tag("button", extract=True)
    def button_tag(self, t: Tag):
        t.string = self.msg

    def add_button(self):
        """Add a button to the component."""
        self.append(self.button_tag)

# Usage
button = Button("Extracted")
print(str(button))  # <div></div>

button.add_button()
print(str(button))  # <div><button class="btn">Extracted</button></div>
```

## Dynamic List Component

Create a component that dynamically generates list items:

```python
from copy import copy

class ListComponent(Component):
    html = """
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
    """

    def __init__(self, list_items: list[str]):
        self.list_items = list_items

    def render(self):
        for item in self.list_items:
            list_item = copy(self.list_item_tag)
            list_item.string = item
            self.append(list_item)

    @tag("li", extract=True)
    def list_item_tag(self):
        pass

    @tag(clear=True)
    def list_tag(self):
        pass

# Usage
list_comp = ListComponent(["one", "two", "three"])
print(str(list_comp))
# <ul><li>one</li><li>two</li><li>three</li></ul>
```

## Component from File

Load component HTML from external file:

```python
class Button(Component):
    html = "./button.html"  # Contents: <button>Test Button</button>

    def __init__(self, msg: str):
        self.msg = msg

    def render(self):
        self.string = self.msg

# Usage
with ui.div() as container:
    Button("Save")
    Button("Edit")
    Button("Delete")

print(str(container))
# <div><button>Save</button><button>Edit</button><button>Delete</button></div>
```
