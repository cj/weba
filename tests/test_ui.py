import asyncio

import pytest

from weba import ui


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
