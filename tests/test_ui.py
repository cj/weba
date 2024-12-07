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
    with ui.div() as form:
        ui.input_(
            type="text", name="search", hx_post="/search", hx_trigger="keyup changed delay:500ms", hx_target="#results"
        )
        with ui.div(id="results"):
            ui.p("Results will appear here...")

    result = str(form)
    # Check that all required attributes are present
    assert "<div>" in result
    assert 'type="text"' in result
    assert 'name="search"' in result
    assert 'hx-post="/search"' in result
    assert 'hx-trigger="keyup changed delay:500ms"' in result
    assert 'hx-target="#results"' in result
    assert '<div id="results">' in result
    assert "<p>Results will appear here...</p>" in result
    assert result.startswith("<div>")
    assert result.endswith("</div>")


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
