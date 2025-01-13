from __future__ import annotations

import pytest

from weba import Component

# def test_ui_raw_with_lxml_parser():
#     """Test that ui.raw correctly handles HTML fragments with lxml parser."""
#     ui_instance = ui.Ui(parser="lxml")
#
#     # Test fragment
#     fragment = "<div>Hello</div>"
#     result = ui_instance.raw(fragment, parser="lxml")
#     assert str(result) == fragment
#
#     # Test full document
#     doc = "<!DOCTYPE html><html><body><div>Hello</div></body></html>"
#     result = ui_instance.raw(doc, parser="lxml")
#     assert "<!DOCTYPE html>" in str(result)
#     assert "<html>" in str(result)


def test_component_with_lxml_parser():
    """Test that Component correctly handles HTML fragments with lxml parser."""

    class TestComponent(Component):
        src = "<div>Hello</div>"
        src_parser = "lxml"

    component = TestComponent()
    assert str(component) == "<div>Hello</div>"

    # Test with full HTML document
    class FullDocComponent(Component):
        src = "<!DOCTYPE html><html><body><div>Hello</div></body></html>"
        src_parser = "lxml"

    component = FullDocComponent()
    assert "<!DOCTYPE html>" in str(component)
    assert "<html>" in str(component)


@pytest.mark.asyncio
async def test_async_component_with_lxml():
    """Test that async components work with lxml parser."""

    class AsyncComponent(Component):
        src = "<div>Hello</div>"
        src_parser = "lxml"

        async def render(self):
            self.string = "Hello World"

    component = await AsyncComponent()
    assert str(component) == "<div>Hello World</div>"
