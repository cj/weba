from __future__ import annotations

import asyncio
import json

import pytest
from bs4 import NavigableString

from weba import Tag, ui

# pyright: reportArgumentType=false, reportOptionalSubscript=false, reportUnknownArgumentType=false


def test_ui_hello_world():
    with ui.div() as html:
        ui.h1("Hello, World!")

    assert "<div><h1>Hello, World!</h1></div>" in str(html)


def test_ui_hello_world_with_subtext():
    with ui.div() as html:
        ui.h1("Hello, World!")
        ui.h2("This is a subtext.")

    assert "<div><h1>Hello, World!</h1><h2>This is a subtext.</h2></div>" in str(html)


def test_ui_test_multiple_blocks():
    with ui.div() as html1:
        ui.h1("Hello, World!")
        ui.h2("This is a subtext.")

    assert "<div><h1>Hello, World!</h1><h2>This is a subtext.</h2></div>" in str(html1)

    with ui.div() as html2:
        ui.h1("Hello, Two!")
        ui.h2("This is a subtext two.")

    assert "<div><h1>Hello, Two!</h1><h2>This is a subtext two.</h2></div>" in str(html2)


def test_ui_context_isolation():
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


def test_ui_attributes():
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


def test_ui_class_list():
    # Test class attribute accepting a list
    with ui.div(class_=["container", "mt-4", "px-2"]) as div:
        pass

    assert str(div) == '<div class="container mt-4 px-2"></div>'


def test_ui_class_manipulation():
    # Test direct class manipulation
    hello_tag = ui.h1("Hello, World!")
    hello_tag["class"].append("highlight")
    hello_tag["class"].append("text-xl")

    assert 'class="highlight text-xl"' in str(hello_tag)


def test_ui_value_to_string_conversion():
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


def test_ui_htmx_search_form():
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


def test_ui_append_to_existing_element():
    def list_item_tag(text: str) -> Tag:
        return ui.li(text)

    with ui.ul() as list_tag:
        ui.li("Item 1")
        ui.li("Item 2")

    list_tag.append(list_item_tag("Item 3"))

    assert "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>" in str(list_tag)


def test_ui_insert_methods():  # sourcery skip: extract-duplicate-method
    # Test insert at specific position
    with ui.ul() as list_tag:
        ui.li("First")
        ui.li("Third")

    second = ui.li("Second")
    list_tag.insert(1, second)

    assert str(list_tag) == "<ul><li>First</li><li>Second</li><li>Third</li></ul>"
    assert second.parent == list_tag
    assert second in list_tag.children

    # Test insert_before
    with ui.div() as container:
        middle = ui.p("Middle")
        ui.p("End")

    start = ui.p("Start")
    middle.insert_before(start)

    assert str(container) == "<div><p>Start</p><p>Middle</p><p>End</p></div>"
    assert start.parent == container
    assert start in container.children

    # Test insert_after
    with ui.div() as container:
        ui.p("Start")
        middle = ui.p("Middle")

    end = ui.p("End")
    middle.insert_after(end)

    assert str(container) == "<div><p>Start</p><p>Middle</p><p>End</p></div>"
    assert end.parent == container
    assert end in container.children

    # Test insert at end position
    with ui.ul() as list_tag:
        ui.li("First")
        ui.li("Second")

    last = ui.li("Last")
    list_tag.insert(2, last)

    assert str(list_tag) == "<ul><li>First</li><li>Second</li><li>Last</li></ul>"
    assert last.parent == list_tag
    assert last in list_tag.children


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


def test_ui_card_component():
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


def test_ui_list_operations():  # sourcery skip: no-loop-in-tests
    # Test extend
    with ui.ul() as list_tag:
        items = [ui.li(f"Item {i}") for i in range(3)]
        list_tag.extend(items)

    assert str(list_tag) == "<ul><li>Item 0</li><li>Item 1</li><li>Item 2</li></ul>"
    assert all(item.parent == list_tag for item in items)
    assert all(item in list_tag.children for item in items)  # pyright: ignore[reportPrivateUsage]

    # Test clear
    list_tag.clear()
    assert str(list_tag) == "<ul></ul>"
    assert len(list_tag.contents) == 0  # pyright: ignore[reportPrivateUsage]
    assert all(item.parent is None for item in items)

    # Test pop
    with ui.ul() as list_tag:
        for i in range(3):
            ui.li(f"Item {i}")

    # Pop from end
    list_tag.contents.pop()
    # last = list_tag.contents.pop()
    # assert str(last) == "<li>Item 2</li>"
    # assert last.parent is None
    # assert last not in list_tag.contents  # pyright: ignore[reportPrivateUsage]

    # Pop from beginning
    list_tag.contents.pop(0)
    # first = list_tag.contents.pop(0)
    # assert str(first) == "<li>Item 0</li>"
    assert str(list_tag) == "<ul><li>Item 1</li></ul>"


def test_ui_tag_attributes():
    # Test non-class attribute access
    with ui.div(id="test", data_value="123") as div:
        assert div["id"] == "test"
        assert div["data-value"] == "123"

    # Test string class attribute handling
    div.attrs["class"] = "existing-class"
    div["class"].append("new-class")
    assert "existing-class new-class" in str(div)

    # Test non-list class attribute handling
    div.attrs["class"] = 42  # Force non-list/non-string value
    assert isinstance(div["class"], list)
    assert len(div["class"]) == 0


def test_ui_select_methods():
    with ui.div() as container:
        ui.p("First", class_="one")
        ui.p("Second", class_="two")

        # Test select method
        paragraphs = container.select("p")
        assert len(paragraphs) == 2
        assert all(p.name == "p" for p in paragraphs)

        # Test find_all method
        found = container.find_all("p")
        assert len(found) == 2
        assert all(p.name == "p" for p in found)


def test_ui_raw_html():
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


def test_ui_raw_multiple_root_elments():
    tag_string = "<div>First</div><div>Second</div>"
    tag = ui.raw(tag_string)

    assert str(tag) == tag_string


def test_ui_text():  # sourcery skip: extract-method, no-conditionals-in-tests
    # Test basic text node
    text = ui.text("Hello World")
    assert str(text) == "Hello World"

    # Test with different types
    assert str(ui.text(42)) == "42"
    assert str(ui.text(3.14)) == "3.14"
    assert str(ui.text(True)) == "True"
    assert not str(ui.text(None))

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
        if (middle := container.find("p", class_="two")) and (next_elem := middle.find_next("div")):
            assert str(next_elem) == '<div class="three">Nested</div>'

            if prev_elem := next_elem.find_previous("p"):
                assert str(prev_elem) == '<p class="two">Second</p>'

    # Test raw with empty/invalid HTML
    empty_tag = ui.raw("")

    assert not str(empty_tag)

    whitespace_tag = ui.raw("   ")

    assert str(whitespace_tag) == "   "


def test_ui_json_attributes():
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


def test_ui_comment_one():
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


def test_ui_comment():
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
    assert container.name == "div"

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


def test_ui_replace_with():
    # Test basic replacement
    with ui.div() as container:
        original = ui.p("Original")
        ui.span("Other")

    replacement = ui.h2("New")
    removed = original.replace_with(replacement)

    assert str(container) == "<div><h2>New</h2><span>Other</span></div>"
    assert removed is original
    assert original.parent is None
    assert replacement.parent is container

    # Test multiple replacements
    with ui.div() as container:
        original = ui.p("Original")
        ui.span("Other")

    new1 = ui.h2("New 1")
    new2 = ui.h3("New 2")
    removed = original.replace_with(new1, new2)

    assert str(container) == "<div><h2>New 1</h2><h3>New 2</h3><span>Other</span></div>"
    assert removed is original
    assert original.parent is None
    assert new1.parent is container
    assert new2.parent is container


def test_ui_insert_before_multiple():
    # Test inserting multiple tags before an existing tag
    with ui.div() as container:
        existing = ui.p("Existing")
        ui.span("After")

    new1 = ui.h1("First")
    new2 = ui.h2("Second")
    new3 = ui.h3("Third")
    existing.insert_before(new1, new2, new3)

    assert str(container) == "<div><h1>First</h1><h2>Second</h2><h3>Third</h3><p>Existing</p><span>After</span></div>"
    assert all(tag.parent == container for tag in [new1, new2, new3])
    assert all(tag in container.children for tag in [new1, new2, new3])  # pyright: ignore[reportPrivateUsage]


def test_ui_insert_after_multiple():
    # Test inserting multiple tags after an existing tag
    with ui.div() as container:
        ui.span("Before")
        existing = ui.p("Existing")

    new1 = ui.h1("First")
    new2 = ui.h2("Second")
    new3 = ui.h3("Third")
    existing.insert_after(new1, new2, new3)

    assert str(container) == "<div><span>Before</span><p>Existing</p><h1>First</h1><h2>Second</h2><h3>Third</h3></div>"
    assert all(tag.parent == container for tag in [new1, new2, new3])
    assert all(tag in container.children for tag in [new1, new2, new3])  # pyright: ignore[reportPrivateUsage]


def test_ui_comment_no_sibling():
    # HTML with a comment but no following sibling
    html = """<div>
    <!-- .button -->
    </div>"""

    container = ui.raw(html)
    results = container.comment(".button")

    # Ensure no results are returned since there is no sibling
    assert results == []


def test_ui_comment_with_text_sibling():
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
    assert isinstance(results[0], NavigableString)


def test_ui_extract():  # sourcery skip: extract-duplicate-method, extract-method
    # Test basic extraction
    with ui.div() as container:
        child = ui.p("Test")
        assert child in container.children  # pyright: ignore[reportPrivateUsage]

        extracted = child.extract()
        assert extracted is child
        assert child.parent is None
        assert child not in container.children  # pyright: ignore[reportPrivateUsage]
        assert str(container) == "<div></div>"

    # Test extraction with known index
    with ui.div() as container:
        ui.span("First")
        middle = ui.p("Middle")
        ui.span("Last")

        index = container.contents.index(middle)
        extracted = middle.extract(index)

        assert extracted is middle
        assert middle.parent is None
        assert middle not in container.children  # pyright: ignore[reportPrivateUsage]
        assert str(container) == "<div><span>First</span><span>Last</span></div>"

    # Test extraction of element without parent
    orphan = ui.p("Orphan")
    extracted = orphan.extract()
    assert extracted is orphan
    assert orphan.parent is None


def test_ui_getattr_behavior():  # sourcery skip: extract-method
    # Test method that returns a single Bs4Tag
    with ui.div() as container:
        ui.p("Test", class_="test-p")
        result = container.find("p", class_="test-p")
        assert isinstance(result, Tag)
        assert str(result) == '<p class="test-p">Test</p>'

    # Test method that returns a list of Bs4Tags
    with ui.div() as container:
        ui.p("First", class_="test-p")
        ui.p("Second", class_="test-p")
        results = container.find_all("p", class_="test-p")
        assert isinstance(results, list)
        assert all(isinstance(r, Tag) for r in results)
        assert len(results) == 2
        assert str(results[0]) == '<p class="test-p">First</p>'
        assert str(results[1]) == '<p class="test-p">Second</p>'

    # Test accessing non-callable attribute
    with ui.div() as container:
        assert container.name == "div"
        assert isinstance(container.name, str)


def test_ui_setting_tag_attributes():
    button_tag = ui.button("Test")

    # Test direct attribute access
    button_tag.string = "Foo"
    assert str(button_tag) == "<button>Foo</button>"

    # Test changing tag name
    button_tag.name = "input"
    assert str(button_tag) == "<input>Foo</input>"

    # Test attrs property
    button_tag.attrs["class"] = "primary"
    assert str(button_tag) == '<input class="primary">Foo</input>'

    # Test attrs with multiple classes
    button_tag.attrs["class"] = ["primary", "large"]
    assert str(button_tag) == '<input class="primary large">Foo</input>'

    # Test other attributes
    button_tag.attrs["data-test"] = "value"
    assert 'data-test="value"' in str(button_tag)


def test_ui_passing_tag_as_argument():
    button_tag = ui.button(ui.span("Hello, World!"))

    assert str(button_tag) == "<button><span>Hello, World!</span></button>"
