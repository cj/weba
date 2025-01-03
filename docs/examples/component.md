# Component Examples

## Basic Component

Create a simple button component:

```python
from weba import Component, ui

class Button(Component):
    src = "<button>Example</button>"

    def __init__(self, msg: str):
        self.msg = msg

    def render(self):
        self.string = self.msg

# Usage
with ui.div() as container:
    Button("Click me")

print(container)
```

Output:

```html
<div>
    <button>Click me</button>
</div>
```

## Replace Root Tag

Components can replace their root tag while preserving contents:

```python
class RootComponent(Component):
    src = "<div>Content <span>here</span></div>"

    def render(self):
        self.replace_root_tag(ui.section(class_="container"))

# Usage
component = RootComponent()
print(component)
```

Output:

```html
<section class="container">Content <span>here</span></section>
```

## Replace Root Tag Using Selector

Components can also replace their root tag based on a selector:

```python
class RootTagComponent(Component):
    src = "<div>Content <span>here</span><section class='container'>Content <span>here</span></section></div>"

    @tag("section", root_tag=True)
    def section(self):
        pass

# Usage
component = RootTagComponent()
print(component)
```

Output:

```html
<section class="container">Content <span>here</span></section>
```

## Using Tag Decorators

Components with tag decorators for more control:

```python
class Button(Component):
    src = "<div><button class='btn'>Example</button></div>"

    def __init__(self, msg: str):
        self.msg = msg

    @tag("button")
    def button_tag(self, t: Tag):
        t.string = self.msg

# Usage
with ui.div() as container:
    Button("Submit")

print(container)
```

Output:

```html
<div>
    <div>
        <button class="btn">Submit</button>
    </div>
</div>
```

## Comment Selectors

Use HTML comments as selectors:

```python
class Button(Component):
    src = """<div><!-- #button --><button>Example</button></div>"""

    def __init__(self, msg: str):
        self.msg = msg

    @tag("<!-- #button -->")
    def button_tag(self, t: Tag):
        t.string = self.msg

# Usage
with ui.div() as container:
    Button("Delete")

print(container)
```

Output:

```html
<div>
    <div>
        <!-- #button -->
        <button>Delete</button>
    </div>
</div>
```

## Async Components

Create components with async rendering:

```python
import asyncio

class AsyncButton(Component):
    src = "<button></button>"

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

    print(container)
```

Output:

```html
<div>
    <button>Async Click Me</button>
    <button>Another Button</button>
</div>
```

## Extract and Clear Tags

Manipulate component structure with extract and clear options:

```python
class Button(Component):
    src = "<div><button class='btn'>Example</button></div>"

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
print(button)

button.add_button()
print(button)
```

Output:

```html
<div></div>
<div>
    <button class="btn">Extracted</button>
</div>
```

## Dynamic List Component

Create a component that dynamically generates list items:

```python
class ListComponent(Component):
    src = """
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
            list_item = self.list_item_tag.copy()
            list_item.string = item
            self.list_tag.append(list_item)

    @tag("li", extract=True)
    def list_item_tag(self):
        pass

    @tag(clear=True)
    def list_tag(self):
        pass

# Usage
list_comp = ListComponent(["one", "two", "three"])
print(list_comp)
```

Output:

```html
<ul>
    <li>one</li>
    <li>two</li>
    <li>three</li>
</ul>
```

## Async Before Render

Components can perform async operations before rendering:

```python
import asyncio

class UserProfile(Component):
    src = "<div><h2></h2><div class='content'></div></div>"

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_data = None

    async def before_render(self):
        # Simulate fetching user data (this would be some async data request)
        await asyncio.sleep(0.1)
        self.user_data = {
            "name": "Alice Smith",
            "bio": "Python Developer"
        }

    def render(self):
        self.select_one("h2").string = self.user_data["name"]

        with self.select_one(".content"):
            ui.p(self.user_data["bio"])

# Usage
async def main():
    profile = await UserProfile("123")
    print(str(profile))
```

Output:

```html
<div>
    <h2>Alice Smith</h2>
    <div class="content">
        <p>Python Developer</p>
    </div>
</div>
```

## Component from File

Load component HTML from external file:

```python
class Button(Component):
    src = "./button.html"  # Contents: <button>Test Button</button>

    def __init__(self, msg: str):
        self.msg = msg

    def render(self):
        self.string = self.msg

# Usage
with ui.div() as container:
    Button("Save")
    Button("Edit")
    Button("Delete")

print(container)
```

Output:

```html
<div>
    <button>Save</button>
    <button>Edit</button>
    <button>Delete</button>
</div>
```

## Using no_tag_context

The `no_tag_context` context manager temporarily disables tag context tracking:

```python
from weba import Component, ui, no_tag_context

class NestedComponent(Component):
    src = "<div><ul></ul></div>"

    def render(self):
        # Normal context - appends to current component
        with self.select_one("ul"):
            ui.li("First item")

        # Disable context tracking - creates standalone tags
        with no_tag_context():
            standalone_li = ui.li("Standalone item")
            # Manually append where needed
            self.select_one("ul").append(standalone_li)

# Usage
with ui.div() as container:
    NestedComponent()

print(container)
```

Output:

```html
<div>
    <div>
        <ul>
            <li>First item</li>
            <li>Standalone item</li>
        </ul>
    </div>
</div>
```

## Component Lifecycle Hooks

Components support `before_render`, `render`, and `after_render` hooks:

```python
class UserProfile(Component):
    src = "<div><h2></h2><p></p></div>"

    def __init__(self):
        self.steps = []

    def before_render(self):
        self.steps.append("before")
        self.name = "Alice Smith"

    def render(self):
        self.steps.append("render")
        self.select_one("h2").string = self.name
        self.select_one("p").string = "Profile loaded"

    def after_render(self):
        self.steps.append("after")
        self.select_one("p").string += " ✓"

# Usage outside context manager - all hooks run immediately
profile = UserProfile()
assert profile.steps == ["before", "render", "after"]
print(profile)  # <div><h2>Alice Smith</h2><p>Profile loaded ✓</p></div>
```

Output:

```html
<div>
    <h2>Alice Smith</h2>
    <p>Profile loaded ✓</p>
</div>
```

### Async Component Lifecycle Hooks

Components can use async hooks for data loading and rendering:

```python
class AsyncProfile(Component):
    src = "<div><h2></h2><p></p></div>"

    async def before_render(self):
        # Simulate fetching user data
        await asyncio.sleep(0.1)
        self.name = "Bob Jones"

    async def render(self):
        self.select_one("h2").string = self.name

    async def after_render(self):
        self.select_one("p").string = "Async loaded"

# Usage with async context manager
async with AsyncProfile() as profile:
    # before_render and render have run
    profile.append(ui.span("Extra content"))
    # after_render runs on context exit

print(profile)  # <div><h2>Bob Jones</h2><p>Async loaded</p><span>Extra content</span></div>

```

Output:

```html
<div>
    <h2>Bob Jones</h2>
    <p>Async loaded</p>
    <span>Extra content</span>
</div>
```

### Or without context manager

```python
profile = await AsyncProfile()
print(profile)  # <div><h2>Bob Jones</h2><p>Async loaded</p></div>
```

Output:

```html
<div>
    <h2>Bob Jones</h2>
    <p>Async loaded</p>
</div>
```

## Select Root Tag from Source

Components can select a new root tag from their source HTML using `src_root_tag`:

```python
class CardComponent(Component):
    src = """
    <div class="wrapper">
        <section class="card">
            <h2>Card Title</h2>
            <p>Card content goes here</p>
        </section>
        <div class="footer">Footer content</div>
    </div>
    """
    # Select the card section as the root, discarding wrapper and footer
    src_root_tag = "section.card"

# Usage
card = CardComponent()
print(card)
```

Output:

```html
<section class="card">
    <h2>Card Title</h2>
    <p>Card content goes here</p>
</section>
```

This is equivalent to using `@tag("section.card", root_tag=True)` but requires less code.

## Replace Component Content

Components can replace their content using tag assignment:

```python
class HelloComponent(Component):
    src = "./layout.html"  # A layout with <body><main></main></body>

    @tag("body > main")
    def main(self):
        pass

    def render(self):
        self.main = ui.raw("<main>Hello</main>")

# Usage with context manager
with HelloComponent() as html:
    html.main.append(ui.text(", World!"))

print(html)  # Contains: <main>Hello, World!</main>
```

Output:

```html
<main>Hello, World!</main>
```

This example shows how to:

1. Select a section of the component using CSS selectors
2. Replace its content by assigning a new tag
3. Modify the replaced content within the context manager
