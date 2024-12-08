import asyncio
import json

import pytest
from bs4 import NavigableString

from weba import Tag, TagAttributeError, TagKeyError, ui


@pytest.mark.asyncio
async def test_ui_hello_world():
    with ui.div() as html:
        ui.h1("Hello, World!")

    assert "<div><h1>Hello, World!</h1></div>" in str(html)


@pytest.mark.asyncio
async def test_ui_hello_world_with_subtext():
    with ui.div() as html:
        ui.h1("Hello, World!")
        ui.h2("This is a subtext.")

    assert "<div><h1>Hello, World!</h1><h2>This is a subtext.</h2></div>" in str(html)


@pytest.mark.asyncio
async def test_ui_test_multiple_blocks():
    with ui.div() as html1:
        ui.h1("Hello, World!")
        ui.h2("This is a subtext.")

    assert "<div><h1>Hello, World!</h1><h2>This is a subtext.</h2></div>" in str(html1)

    with ui.div() as html2:
        ui.h1("Hello, Two!")
        ui.h2("This is a subtext two.")

    assert "<div><h1>Hello, Two!</h1><h2>This is a subtext two.</h2></div>" in str(html2)


@pytest.mark.asyncio
async def test_ui_context_isolation():
    # First block
    with ui.div() as outer:
        ui.p("Outer paragraph")

        # Nested block
        with ui.div() as inner:
            ui.p("Inner paragraph")

        # Verify inner content
        assert "<div><p>Inner paragraph</p></div>" in str(inner)

        # This should be added to outer, not inner
        ui.p("Another outer paragraph")

    expected = "<div><p>Outer paragraph</p><div><p>Inner paragraph</p></div><p>Another outer paragraph</p></div>"

    assert expected in str(outer)


@pytest.mark.asyncio
async def test_ui_async_context_isolation():
    async def task1():
        with ui.div() as div1:
            ui.p("Task 1 paragraph")
            ui.p("Task 1 second paragraph")
        return div1

    async def task2():
        with ui.div() as div2:
            ui.p("Task 2 paragraph")
            ui.p("Task 2 second paragraph")
        return div2

    # Run both tasks concurrently
    div1, div2 = await asyncio.gather(task1(), task2())

    # Verify each task maintained its own context
    assert str(div1) == "<div><p>Task 1 paragraph</p><p>Task 1 second paragraph</p></div>"
    assert str(div2) == "<div><p>Task 2 paragraph</p><p>Task 2 second paragraph</p></div>"


@pytest.mark.asyncio
async def test_ui_attributes():
    # Test regular attributes
    with ui.div(class_="container", data_test="value") as div1:
        pass

    assert str(div1) == '<div class="container" data-test="value"></div>'

    # Test boolean attributes
    with ui.div(hx_boost=True) as div2:
        pass

    assert str(div2) == "<div hx-boost></div>"

    # Test nested elements with attributes
    with ui.div(class_="outer") as div3:
        ui.p(class_="inner", data_value="test")

    assert str(div3) == '<div class="outer"><p class="inner" data-value="test"></p></div>'


@pytest.mark.asyncio
async def test_ui_class_list():
    # Test class attribute accepting a list
    with ui.div(class_=["container", "mt-4", "px-2"]) as div:
        pass

    assert str(div) == '<div class="container mt-4 px-2"></div>'


@pytest.mark.asyncio
async def test_ui_class_manipulation():
    # Test direct class manipulation
    hello_tag = ui.h1("Hello, World!")
    hello_tag["class"].append("highlight")
    hello_tag["class"].append("text-xl")

    assert 'class="highlight text-xl"' in str(hello_tag)


@pytest.mark.asyncio
async def test_ui_value_to_string_conversion():
    number_tag = ui.p(123)
    assert str(number_tag) == "<p>123</p>"

    float_tag = ui.p(3.14159)
    assert str(float_tag) == "<p>3.14159</p>"

    bool_tag = ui.p(True)
    assert str(bool_tag) == "<p>True</p>"

    none_tag = ui.p(None)
    assert str(none_tag) == "<p></p>"

    from datetime import datetime

    date = datetime(2024, 12, 25, 12, 0)
    date_tag = ui.p(date)
    assert str(date_tag) == "<p>2024-12-25 12:00:00</p>"


@pytest.mark.asyncio
async def test_ui_htmx_search_form():
    with ui.form() as form:
        ui.input_(
            type="text", name="search", hx_post="/search", hx_trigger="keyup changed delay:500ms", hx_target="#results"
        )
        with ui.div(id="results"):
            ui.p("Results will appear here...")

    result = str(form)
    # Check that all required attributes are present
    assert "<form>" in result
    assert 'type="text"' in result
    assert 'name="search"' in result
    assert 'hx-post="/search"' in result
    assert 'hx-trigger="keyup changed delay:500ms"' in result
    assert 'hx-target="#results"' in result
    assert '<div id="results">' in result
    assert "<p>Results will appear here...</p>" in result
    assert result.startswith("<form>")
    assert result.endswith("</form>")


@pytest.mark.asyncio
async def test_ui_append_to_existing_element():
    def list_item_tag(text: str) -> Tag:
        return ui.li(text)

    with ui.ul() as list_tag:
        ui.li("Item 1")
        ui.li("Item 2")

    list_tag.append(list_item_tag("Item 3"))

    assert "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>" in str(list_tag)


@pytest.mark.asyncio
async def test_ui_replace_with():
    with ui.div() as container:
        original = ui.p("Original content")
        ui.div("Other content")

    replacement = ui.h2("New content")
    original.replace_with(replacement)

    assert "<div><h2>New content</h2><div>Other content</div></div>" in str(container)

    with ui.div() as container:
        ui.h1("Hello, World!")
        ui.h2("This is a subtext.")

    container.select_one("h1").replace_with(ui.h3("New heading"))

    assert "<h1>Hello, World!</h1>" not in str(container)
    assert "<h3>New heading</h3>" in str(container)


@pytest.mark.asyncio
async def test_ui_insert_methods():
    # Test insert at specific position
    with ui.ul() as list_tag:
        ui.li("First")
        ui.li("Third")

    second = ui.li("Second")
    list_tag.insert(1, second)

    assert str(list_tag) == "<ul><li>First</li><li>Second</li><li>Third</li></ul>"
    assert second.parent == list_tag
    assert second in list_tag._children  # pyright: ignore[reportPrivateUsage]

    # Test insert_before
    with ui.div() as container:
        middle = ui.p("Middle")
        ui.p("End")

    start = ui.p("Start")
    middle.insert_before(start)

    assert str(container) == "<div><p>Start</p><p>Middle</p><p>End</p></div>"
    assert start.parent == container
    assert start in container._children  # pyright: ignore[reportPrivateUsage]

    # Test insert_after
    with ui.div() as container:
        ui.p("Start")
        middle = ui.p("Middle")

    end = ui.p("End")
    middle.insert_after(end)

    assert str(container) == "<div><p>Start</p><p>Middle</p><p>End</p></div>"
    assert end.parent == container
    assert end in container._children  # pyright: ignore[reportPrivateUsage]

    # Test insert at end position
    with ui.ul() as list_tag:
        ui.li("First")
        ui.li("Second")

    last = ui.li("Last")
    list_tag.insert(2, last)

    assert str(list_tag) == "<ul><li>First</li><li>Second</li><li>Last</li></ul>"
    assert last.parent == list_tag
    assert last in list_tag._children  # pyright: ignore[reportPrivateUsage]


def create_card(
    title: str,
    content: str,
    items: list[str] | None = None,
    button_text: str | None = None,
    button_class: str = "btn",
) -> Tag:
    """Create a card component with customizable content.

    Args:
        title: The card's header title
        content: The main content text
        items: Optional list items to display
        button_text: Optional button text (no button if None)
        button_class: CSS class for the button (defaults to "btn")

    Returns:
        Tag: The constructed card component
    """
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


@pytest.mark.asyncio
async def test_ui_card_component():
    # Test basic card
    card1 = create_card(
        title="Card Title", content="Card content goes here", items=["Item 1", "Item 2"], button_text="Click me!"
    )

    expected1 = (
        '<div class="card">'
        '<div class="card-header"><h2>Card Title</h2></div>'
        '<div class="card-body"><p>Card content goes here</p>'
        '<ul class="list"><li>Item 1</li><li>Item 2</li></ul></div>'
        '<div class="card-footer"><button class="btn">Click me!</button></div>'
        "</div>"
    )
    assert expected1 in str(card1)

    # Test card without button
    card2 = create_card(title="Simple Card", content="Just some content", items=["Only item"])

    expected2 = (
        '<div class="card">'
        '<div class="card-header"><h2>Simple Card</h2></div>'
        '<div class="card-body"><p>Just some content</p>'
        '<ul class="list"><li>Only item</li></ul></div>'
        "</div>"
    )
    assert expected2 in str(card2)

    # Test card without items
    card3 = create_card(
        title="No Items", content="A card without a list", button_text="Submit", button_class="btn-primary"
    )

    expected3 = (
        '<div class="card">'
        '<div class="card-header"><h2>No Items</h2></div>'
        '<div class="card-body"><p>A card without a list</p></div>'
        '<div class="card-footer"><button class="btn-primary">Submit</button></div>'
        "</div>"
    )
    assert expected3 in str(card3)


@pytest.mark.asyncio
async def test_ui_tag_attributes():
    # Test non-class attribute access
    with ui.div(id="test", data_value="123") as div:
        assert div["id"] == "test"
        assert div["data-value"] == "123"

    # Test string class attribute handling
    div.tag.attrs["class"] = "existing-class"
    div["class"].append("new-class")
    assert "existing-class new-class" in str(div)

    # Test non-list class attribute handling
    div.tag.attrs["class"] = 42  # Force non-list/non-string value
    assert isinstance(div["class"], list)
    assert len(div["class"]) == 0

    # Test NavigableString key access
    text_node = Tag(NavigableString("test"))  # pyright: ignore[reportArgumentType]
    with pytest.raises(TagKeyError) as exc_info:
        text_node["class"]
    assert "NavigableString" in str(exc_info.value)
    assert "class" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ui_wrap_tag():
    # Test None tag handling
    assert ui.div().wrap_tag(None) is None

    # Test parent-child relationship
    with ui.div() as parent:
        child = ui.p("test")
        parent.append(child)
        assert child.parent == parent
        assert child in parent._children  # pyright: ignore[reportPrivateUsage]


@pytest.mark.asyncio
async def test_ui_select_methods():
    with ui.div() as container:
        ui.p("First", class_="one")
        ui.p("Second", class_="two")

        # Test select method
        paragraphs = container.select("p")
        assert len(paragraphs) == 2
        assert all(p.tag.name == "p" for p in paragraphs)

        # Test find_all method
        found = container.find_all("p")
        assert len(found) == 2
        assert all(p.tag.name == "p" for p in found)


@pytest.mark.asyncio
async def test_ui_raw_html():
    # Test basic HTML parsing
    tag = ui.raw("<div>Hello World</div>")
    tag["class"].append("raw")
    assert str(tag) == '<div class="raw">Hello World</div>'

    # Test nested HTML
    tag = ui.raw('<div class="container"><p>Content</p><span>More</span></div>')
    assert '<div class="container"><p>Content</p><span>More</span></div>' in str(tag)

    # Test handling of invalid HTML
    tag = ui.raw("Not HTML")
    assert str(tag) == "Not HTML"  # Falls back to plain text

    # Test complex HTML with attributes
    complex_html = """
        <article class="post" data-id="123">
            <h2>Title</h2>
            <div class="content">
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
            </div>
        </article>
    """
    tag = ui.raw(complex_html)
    result = str(tag)
    assert '<article class="post" data-id="123">' in result
    assert "<h2>Title</h2>" in result
    assert '<div class="content">' in result
    assert "<p>Paragraph 1</p>" in result
    assert "<p>Paragraph 2</p>" in result

    # Test raw HTML in context
    with ui.div() as container:
        ui.raw("<p>First paragraph</p>")
        ui.raw("<p>Second paragraph</p>")

    assert str(container) == "<div><p>First paragraph</p><p>Second paragraph</p></div>"


@pytest.mark.asyncio
async def test_ui_parent_child_exit():
    # Test parent-child relationship in __exit__
    parent = Tag(ui.raw("<div>").tag)
    child = Tag(ui.raw("<p>").tag, parent=None)

    # Simulate entering and exiting context with parent-child relationship
    child.parent = parent
    child.__exit__(None, None, None)

    assert child in parent._children  # pyright: ignore[reportPrivateUsage]


@pytest.mark.asyncio
async def test_ui_non_callable_attr():
    # Test accessing a non-callable attribute
    tag = ui.raw("<div>").tag
    tag.string = "test"  # Use BeautifulSoup's built-in string attribute
    wrapped = Tag(tag)

    # This should now return the string attribute
    assert wrapped.string == "test"


@pytest.mark.asyncio
async def test_ui_nonexistent_attr():
    # Test accessing a non-existent attribute
    tag = Tag(ui.raw("<div>").tag)

    # Test attribute that doesn't exist at all
    with pytest.raises(TagAttributeError):
        tag.nonexistent_attr  # noqa: B018

    # Test attribute that exists but is None
    tag.tag.test_attr = None  # pyright: ignore[reportAttributeAccessIssue]

    with pytest.raises(TagAttributeError):
        tag.test_attr  # noqa: B018

    # Test attribute that exists but disappears (race condition simulation)
    tag.tag.temp_attr = "test"  # pyright: ignore[reportAttributeAccessIssue]

    delattr(tag.tag, "temp_attr")  # This will make hasattr true but getattr fail

    with pytest.raises(TagAttributeError):
        tag.temp_attr  # noqa: B018

    # Test attribute that truly doesn't exist by mocking hasattr
    from unittest.mock import patch

    with patch("builtins.hasattr", return_value=False), pytest.raises(TagAttributeError):
        tag.nonexistent_attr  # noqa: B018


@pytest.mark.asyncio
async def test_ui_text():
    # Test basic text node
    text = ui.text("Hello World")
    assert str(text) == "Hello World"

    # Test with different types
    assert str(ui.text(42)) == "42"
    assert str(ui.text(3.14)) == "3.14"
    assert str(ui.text(True)) == "True"
    assert str(ui.text(None)) == "None"

    # Test in context
    with ui.div() as container:
        ui.text("First")
        ui.text("Second")

    assert str(container) == "<div>FirstSecond</div>"

    # Test with nested content
    with ui.p() as para:
        ui.text("Start ")
        with ui.strong():
            ui.text("middle")
        ui.text(" end")

    assert str(para) == "<p>Start <strong>middle</strong> end</p>"

    # Test Tag.__getattr__ with various BeautifulSoup methods
    with ui.div() as container:
        ui.p("First", class_="one")
        ui.p("Second", class_="two")
        ui.div("Nested", class_="three")

        # Test select_one
        first = container.select_one("p.one")
        assert str(first) == '<p class="one">First</p>'

        # Test find
        second = container.find("p", class_="two")
        assert str(second) == '<p class="two">Second</p>'

        # Test select
        all_p = container.select("p")
        assert len(all_p) == 2
        assert str(all_p[0]) == '<p class="one">First</p>'

        # Test find_all
        divs = container.find_all("div")
        assert len(divs) == 1
        assert str(divs[0]) == '<div class="three">Nested</div>'

        # Test find_next and find_previous
        middle = container.find("p", class_="two")
        next_elem = middle.find_next("div")
        assert str(next_elem) == '<div class="three">Nested</div>'
        prev_elem = next_elem.find_previous("p")
        assert str(prev_elem) == '<p class="two">Second</p>'

        # # Test Tag.__getattr__ with non-existent attribute
        with pytest.raises(TagAttributeError):
            container.nonexistent_method()

    # Test raw with empty/invalid HTML
    empty_tag = ui.raw("")

    assert not str(empty_tag)

    whitespace_tag = ui.raw("   ")

    assert str(whitespace_tag) == "   "


@pytest.mark.asyncio
async def test_ui_json_attributes():
    # Test dictionary attribute
    data = {"name": "John", "age": 30}
    with ui.div(data_user=data) as div:
        # Parse and compare as JSON to ignore formatting differences
        assert json.loads(div["data-user"]) == data

    # Test array attribute
    items = ["apple", "banana", "orange"]
    with ui.div(data_items=items) as div:
        assert json.loads(div["data-items"]) == items

    # Test nested structures
    complex_data = {"user": {"name": "John", "age": 30}, "items": ["apple", "banana"], "active": True}
    with ui.div(data_complex=complex_data) as div:
        assert json.loads(div["data-complex"]) == complex_data

    # Test empty containers
    with ui.div(data_empty_obj={}, data_empty_arr=[]) as div:
        assert div["data-empty-obj"] == "{}"
        assert div["data-empty-arr"] == "[]"


@pytest.mark.asyncio
async def test_ui_comment_one():
    # Test finding a single element after a comment
    html = """<div>
    <!-- #button -->
    <button>click me</button>
    <!-- .some-text -->
    Some Text
    </div>"""

    container = ui.raw(html)
    button = container.comment_one("#button")
    assert button is not None
    assert str(button) == "<button>click me</button>"

    # Test with no matching comment
    assert container.comment_one("#nonexistent") is None

    # Test with comment but no following tag
    html = "<div><!-- #empty --></div>"
    container = ui.raw(html)
    assert container.comment_one("#empty") is None

    # Test with comment followed by plain text
    html = """<div>
    <!-- .some-text -->
    Some Text
    </div>"""
    container = ui.raw(html)
    text_node = container.comment_one(".some-text")
    assert text_node is not None
    assert str(text_node) == "Some Text"


@pytest.mark.asyncio
async def test_ui_comment():
    # Test finding multiple elements after comments
    html = """<div>
    <!-- .button -->
    <button>first</button>
    <!-- .button -->
    <button>second</button>
    <!-- .button -->
    <button>third</button>
    </div>"""

    container = ui.raw(html)
    buttons = container.comment(".button")
    assert len(buttons) == 3
    assert str(buttons[0]) == "<button>first</button>"
    assert str(buttons[1]) == "<button>second</button>"
    assert str(buttons[2]) == "<button>third</button>"

    # Test with no matching comments
    assert container.comment(".nonexistent") == []

    # Test with comment followed by another comment
    html = """<div>
    <!-- #button -->
    <!-- #another -->
    </div>"""
    container = ui.raw(html)
    next_node = container.comment_one("#button")
    assert next_node is not None
    assert str(next_node) == "#another"

    # Test with comment at the end of its parent (no next sibling)
    html = """<div>
    <p>Some content</p>
    <!-- #last -->
    </div>"""
    container = ui.raw(html)
    next_node = container.comment_one("#last")
    assert next_node is None

    # Test with mixed content and empty nodes
    html = """<div>
    <!-- .item -->


    <button>a button</button>
    <p>not matched</p>
    <!-- .item -->

    <span>a span</span>
    <!-- non-tag content -->
    This is some text.
    </div>"""

    container = ui.raw(html)

    # Test a method that returns a direct result
    assert container.tag.name == "div"

    items = container.comment(".item")
    assert len(items) == 2
    assert str(items[0]) == "<button>a button</button>"
    assert str(items[1]) == "<span>a span</span>"

    # Test with a mixed
    html = """<div>
    <!-- .mixed -->
    This is some text.
    <!-- .mixed -->
    Another piece of text.
    <!-- .mixed -->
    <span>in a span</span>
    </div>"""

    container = ui.raw(html)
    mixed = container.comment(".mixed")

    assert len(mixed) == 3
    assert str(mixed[0]) == "This is some text."
    assert str(mixed[1]) == "Another piece of text."
    assert str(mixed[2]) == "<span>in a span</span>"


@pytest.mark.asyncio
async def test_ui_replace_with_no_parent():
    # Create tags without a parent
    original = Tag(ui.raw("<p>Original content</p>").tag)
    replacement = Tag(ui.raw("<h2>Replacement content</h2>").tag)

    # Call replace_with when _parent is None
    original.replace_with(replacement)

    # Verify that the replacement occurred in the DOM
    assert str(original.tag) != str(replacement.tag)
    assert str(replacement.tag) == "<h2>Replacement content</h2>"


@pytest.mark.asyncio
async def test_ui_insert_before_no_parent():
    # Create tags without a parent
    existing = Tag(ui.raw("<p>Existing content</p>").tag)
    new_tag = Tag(ui.raw("<h2>New content</h2>").tag)

    # Call insert_before when _parent is None
    existing.insert_before(new_tag)

    # Verify that the DOM structure reflects the insertion
    assert str(existing.tag.previous_sibling) == "<h2>New content</h2>"
    assert str(new_tag.tag.next_sibling) == "<p>Existing content</p>"


@pytest.mark.asyncio
async def test_ui_insert_after_no_parent():
    # Create tags without a parent
    existing = Tag(ui.raw("<p>Existing content</p>").tag)
    new_tag = Tag(ui.raw("<h2>New content</h2>").tag)

    # Call insert_after when _parent is None
    existing.insert_after(new_tag)

    # Verify that the DOM structure reflects the insertion
    assert str(existing.tag.next_sibling) == "<h2>New content</h2>"
    assert str(new_tag.tag.previous_sibling) == "<p>Existing content</p>"


@pytest.mark.asyncio
async def test_ui_wrap_tag_no_parent_relationship():
    # Create a tag with a parent different from the current tag
    other_tag = Tag(ui.raw("<div>").tag)
    child_tag = Tag(ui.raw("<p>Child content</p>").tag)

    # Simulate a different parent
    other_tag.add_child(child_tag)  # Sets child_tag.parent = other_tag

    # Wrap the tag in a different context
    new_wrapper = Tag(ui.raw("<section>").tag)
    wrapped = new_wrapper.wrap_tag(child_tag.tag)

    # Assert the wrapped tag is not added as a child
    assert wrapped is not None
    assert wrapped.parent is None  # No parent relationship established with new_wrapper
    assert wrapped not in new_wrapper._children  # pyright: ignore[reportPrivateUsage]

    # Verify the tag's original parent remains unchanged
    assert child_tag.parent == other_tag


@pytest.mark.asyncio
async def test_ui_comment_no_sibling():
    # HTML with a comment but no following sibling
    html = """<div>
    <!-- .button -->
    </div>"""

    container = ui.raw(html)
    results = container.comment(".button")

    # Ensure no results are returned since there is no sibling
    assert results == []


@pytest.mark.asyncio
async def test_ui_comment_with_text_sibling():
    # HTML with a comment followed by plain text (NavigableString)
    html = """<div>
    <!-- .text -->
    This is a plain text node.
    </div>"""

    # Parse the container
    container = ui.raw(html)

    # Call the `comment` method
    results = container.comment(".text")

    # Ensure the NavigableString is correctly wrapped and added to results
    assert len(results) == 1
    assert str(results[0]) == "This is a plain text node."
    assert isinstance(results[0].tag, NavigableString)
