import asyncio

import pytest

from weba import Tag, ui


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
    assert str(none_tag) == "<p>None</p>"

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
    assert str(tag) == "<div></div>"  # Falls back to empty div

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
