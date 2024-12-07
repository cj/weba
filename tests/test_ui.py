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
