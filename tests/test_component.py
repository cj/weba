import asyncio

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


def test_basic_component_root_tag():
    with ui.div() as container:
        button = Button("Click me")

    button._root_tag.name = "span"  # pyright: ignore[reportPrivateUsage]

    assert str(container) == "<div><span>Click me</span></div>"


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


# def test_component_with_clear():
#     class Button(Component):
#         html = "<div><button class='btn'>Example</button></div>"
#
#         @tag("button", clear=True)
#         def button_tag(self):
#             pass
#
#     with ui.div() as container:
#         Button()
#
#     assert str(container) == '<div><button class="btn"></button></div>'
#
#
# def test_component_with_extract_and_clear():
#     class Button(Component):
#         html = "<div><button class='btn'>Example</button></div>"
#
#         def __init__(self, msg: str):
#             self.msg = msg
#
#         @tag("button", extract=True, clear=True)
#         def button_tag(self, t: Tag):
#             t.string = self.msg
#
#     with ui.div() as container:
#         Button("Extracted and Cleared")
#
#     assert str(container) == "<div></div>"
#
#     class List(Component):
#         html = "<ul></ul>"
#
#     assert str(List()) == "<ul></ul>"
#
#     with List() as html:
#         ui.li("item 1")
#         ui.li("item 2")
#
#     assert str(html) == "<ul><li>item 1</li><li>item 2</li></ul>"


# def test_missing_html_attribute():
#     class InvalidComponent(Component):
#         pass
#
#     with pytest.raises(ValueError, match="Component must define 'html' class variable"):
#         InvalidComponent()
#
#
# def test_missing_template_file():
#     class InvalidComponent(Component):
#         html = "nonexistent.html"
#
#     with pytest.raises(FileNotFoundError, match="Template file not found"):
#         InvalidComponent()
#
#
# def test_multiple_components_in_list():
#     class Button(Component):
#         html = "<button></button>"
#
#         def __init__(self, text: str):
#             self.text = text
#
#         def render(self):
#             self.string = self.text
#
#     with ui.ul() as button_list:
#         with ui.li():
#             Button("first")
#         with ui.li():
#             Button("second")
#             Button("third")
#
#     expected = "<ul><li><button>first</button></li><li><button>second</button><button>third</button></li></ul>"
#     assert str(button_list) == expected
