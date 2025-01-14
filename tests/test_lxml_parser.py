from __future__ import annotations

from unittest import mock

import pytest

from weba import Component, Ui, tag, ui


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


def test_parser_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that parsers respect environment variables like WEBA_LRU_CACHE_SIZE."""
    # Reset cached values
    Ui._html_parser = None  # pyright: ignore[reportPrivateUsage]
    Ui._xml_parser = None  # pyright: ignore[reportPrivateUsage]

    # Test default values
    assert Ui.get_html_parser() == "html.parser"
    assert Ui.get_xml_parser() == "xml"

    Ui._html_parser = "lxml"  # pyright: ignore[reportPrivateUsage]
    assert Ui.get_html_parser() == "lxml"
    Ui._xml_parser = "lxml-xml"  # pyright: ignore[reportPrivateUsage]
    assert Ui.get_xml_parser() == "lxml-xml"

    # Test custom HTML parser
    with monkeypatch.context() as mp:
        mp.setenv("WEBA_HTML_PARSER", "lxml")
        Ui._html_parser = None  # Reset cache # pyright: ignore[reportPrivateUsage]
        assert Ui.get_html_parser() == "lxml"

    # Test custom XML parser
    with monkeypatch.context() as mp:
        mp.setenv("WEBA_XML_PARSER", "lxml-xml")
        Ui._xml_parser = None  # Reset cache# pyright: ignore[reportPrivateUsage]
        assert Ui.get_xml_parser() == "lxml-xml"


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


def test_parser_lxml_with_layout():
    with mock.patch("weba.Ui") as u:
        u._html_parser = "lxmls"

        class Layout(Component):
            src = "./layout.html"

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

        assert str(layout).startswith("<!doctype html>")
        assert "<html" in str(layout)
        assert "<header" in str(layout)
        assert "<main" in str(layout)
        assert "<footer" in str(layout)

        with layout as html:
            with html.header:
                ui.nav("navbar")

            with html.main:
                ui.h1("Hello, World!")

            with html.footer:
                ui.span("contact us")

        html_str = str(html)

        print(html_str)

        assert "<header><nav>navbar</nav></header>" in html_str
        assert "<main><h1>Hello, World!</h1></main>" in html_str
        assert "<footer><span>contact us</span></footer>" in html_str
