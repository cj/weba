import asyncio

from bs4 import Doctype
import pytest

from weba import Component, Tag, tag, ui


class Button(Component):
    html = "<button>Example</button>"

    def __init__(self, msg: str):
        self.msg = msg

    def render(self):
        self.set_message()

    def set_message(self):
        self.string = self.msg


def test_basic_component():
    with ui.div() as container:
        Button("Click me")

    assert str(container) == "<div><button>Click me</button></div>"


def test_component_with_tag_decorator_passing_tag():
    class Button(Component):
        html = "<div><button class='btn'>Example</button></div>"

        def __init__(self, msg: str):
            self.msg = msg

        @tag("button")
        def button_tag(self, t: Tag):
            t.string = self.msg

    with ui.div() as container:
        Button("Submit")

    assert str(container) == '<div><div><button class="btn">Submit</button></div></div>'


def test_component_with_tag_decorator():
    class Button(Component):
        html = "<div><button class='btn'>Example</button></div>"

        def __init__(self, msg: str):
            self.msg = msg

        def render(self):
            self.button_tag.string = "Submit"

        @tag("button")
        def button_tag(self):
            pass

    with ui.div() as container:
        Button("Submit")

    assert str(Button("Foo")) == '<div><button class="btn">Submit</button></div>'
    assert str(container) == '<div><div><button class="btn">Submit</button></div></div>'


def test_component_with_comment_selector():
    class Button(Component):
        html = """<div><!-- #button --><button>Example</button></div>"""

        def __init__(self, msg: str):
            self.msg = msg

        @tag("<!-- #button -->")
        def button_tag(self, t: Tag):
            t.string = self.msg

    with ui.div() as container:
        Button("Delete")

    assert str(container) == "<div><div><!-- #button --><button>Delete</button></div></div>"


@pytest.mark.asyncio
async def test_component_async_context_isolation():
    """Test that components maintain proper context isolation in async tasks."""

    class SimpleCard(Component):
        html = '<div class="card"><!-- #content --><div class="content"></div></div>'

        def __init__(self, title: str, msg: str):
            self.title = title
            self.msg = msg

        @tag("<!-- #content -->")
        def content_tag(self, t: Tag):
            with t:
                ui.h2(self.title)
                ui.p(self.msg)

    async def task1():
        with ui.div() as div1:
            SimpleCard("Task 1", "First paragraph")
            SimpleCard("Task 1", "Second paragraph")
        return div1

    async def task2():
        with ui.div() as div2:
            SimpleCard("Task 2", "First paragraph")
            SimpleCard("Task 2", "Second paragraph")
        return div2

    # Run both tasks concurrently
    div1, div2 = await asyncio.gather(task1(), task2())

    # Verify each task maintained its own context
    expected1 = (
        "<div>"
        '<div class="card"><!-- #content --><div class="content"><h2>Task 1</h2><p>First paragraph</p></div></div>'
        '<div class="card"><!-- #content --><div class="content"><h2>Task 1</h2><p>Second paragraph</p></div></div>'
        "</div>"
    )
    expected2 = (
        "<div>"
        '<div class="card"><!-- #content --><div class="content"><h2>Task 2</h2><p>First paragraph</p></div></div>'
        '<div class="card"><!-- #content --><div class="content"><h2>Task 2</h2><p>Second paragraph</p></div></div>'
        "</div>"
    )
    assert str(div1) == expected1
    assert str(div2) == expected2


def test_component_from_file():
    class Button(Component):
        html = "./button.html"

        def __init__(self, msg: str):
            self.msg = msg

        def render(self):
            self.string = self.msg

    with ui.div() as container:
        Button("Save")
        Button("Edit")
        Button("Delete")

    assert str(container) == "<div><button>Save</button><button>Edit</button><button>Delete</button></div>"


def test_component_empty():
    class UiList(Component):
        html = "<ul></ul>"

    assert str(UiList()) == "<ul></ul>"


def test_component_with_extract():
    class Button(Component):
        html = "<div><button class='btn'>Example</button></div>"

        def __init__(self, msg: str):
            self.msg = msg

        @tag("button", extract=True)
        def button_tag(self, t: Tag):
            t.string = self.msg

        def add_button(self):
            """Button that adds a button to the component."""
            self.append(self.button_tag)

    button = Button("Extracted")

    assert str(button) == "<div></div>"

    button.add_button()

    assert str(button) == '<div><button class="btn">Extracted</button></div>'


def test_component_with_clear():
    class Button(Component):
        html = "<div><button class='btn'>Example</button></div>"

        @tag("button", clear=True)
        def button_tag(self):
            pass

    assert str(Button()) == '<div><button class="btn"></button></div>'


def test_component_with_extract_and_clear():
    class Button(Component):
        html = "<div><button class='btn'>Example</button></div>"

        @tag("button", extract=True, clear=True)
        def button_tag(self):
            pass

    button = Button()

    assert str(button) == "<div></div>"
    assert str(button.button_tag) == '<button class="btn"></button>'


def test_component_context_manager():
    class List(Component):
        html = "<ul></ul>"

    assert str(List()) == "<ul></ul>"

    with List() as html:
        ui.li("item 1")
        ui.li("item 2")

    assert str(html) == "<ul><li>item 1</li><li>item 2</li></ul>"


def test_multiple_components_in_list():
    class Button(Component):
        html = "<button></button>"

        def __init__(self, msg: str):
            self.msg = msg

        def render(self):
            self.string = self.msg

    with ui.ul() as button_list:
        with ui.li():
            Button("first")

        with ui.li():
            Button("second")
            Button("third")

    expected = "<ul><li><button>first</button></li><li><button>second</button><button>third</button></li></ul>"

    assert str(button_list) == expected


@pytest.mark.asyncio
async def test_async_component_context_isolation():
    """Test that async components maintain proper context isolation."""

    class AsyncCard(Component):
        html = '<div class="card"><h2></h2><p></p></div>'

        def __init__(self, title: str, content: str):
            self.title = title
            self.content = content

        async def render(self):
            await asyncio.sleep(0.01)
            self.header_tag.string = self.title
            self.paragraph_tag.string = self.content

        @tag("h2")
        def header_tag(self):
            pass

        @tag("p")
        def paragraph_tag(self):
            pass

    async def task1():
        with ui.div() as div1:
            await AsyncCard("Task 1 Title", "Task 1 Content")
            await AsyncCard("Task 1 Second", "Task 1 More Content")
        return div1

    async def task2():
        with ui.div() as div2:
            await AsyncCard("Task 2 Title", "Task 2 Content")
            await AsyncCard("Task 2 Second", "Task 2 More Content")
        return div2

    # Run both tasks concurrently
    div1, div2 = await asyncio.gather(task1(), task2())

    # Verify each task maintained its own context
    expected1 = (
        "<div>"
        '<div class="card"><h2>Task 1 Title</h2><p>Task 1 Content</p></div>'
        '<div class="card"><h2>Task 1 Second</h2><p>Task 1 More Content</p></div>'
        "</div>"
    )
    expected2 = (
        "<div>"
        '<div class="card"><h2>Task 2 Title</h2><p>Task 2 Content</p></div>'
        '<div class="card"><h2>Task 2 Second</h2><p>Task 2 More Content</p></div>'
        "</div>"
    )
    assert str(div1) == expected1
    assert str(div2) == expected2


@pytest.mark.asyncio
async def test_async_component():
    class AsyncButton(Component):
        html = "<button></button>"

        def __init__(self, msg: str):
            self.msg = msg

        async def render(self):
            await asyncio.sleep(0.01)  # Simulate an async operation
            self.string = self.msg

    with ui.div() as container:
        await AsyncButton("Async Click Me")
        await AsyncButton("Async Click Me!")

    assert str(container) == "<div><button>Async Click Me</button><button>Async Click Me!</button></div>"


def test_component_with_layout():
    class Layout(Component):
        html = "./layout.html"

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

    layout = Layout()

    assert "DOCTYPE HTML" in str(layout)
    assert "html" in str(layout)
    assert "header" in str(layout)
    assert "main" in str(layout)
    assert "footer" in str(layout)

    with layout as html:
        with html.main:
            ui.h1("Hello, World!")

    assert "<main><h1>Hello, World!</h1></main>" in str(html)
