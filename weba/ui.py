from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, ClassVar

from bs4 import BeautifulSoup, NavigableString
from bs4 import Tag as BeautifulSoupTag
from charset_normalizer import from_bytes

from weba.errors import UiEncodingError

from .tag import Tag, current_tag_context

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Sequence


class Ui:
    """A factory class for creating UI elements using BeautifulSoup."""

    _html_parser: ClassVar[str | None] = None
    _xml_parser: ClassVar[str | None] = None

    @classmethod
    def get_html_parser(cls) -> str | None:
        """Get the LRU cache size from environment variable."""
        if cls._html_parser is None:
            cls._html_parser = os.getenv("WEBA_HTML_PARSER", "html.parser")

        return cls._html_parser

    @classmethod
    def get_xml_parser(cls) -> str | None:
        """Get the XML parser from environment variable."""
        if cls._xml_parser is None:
            cls._xml_parser = os.getenv("WEBA_XML_PARSER", "xml")

        return cls._xml_parser

    def text(self, html: str | int | float | Sequence[Any] | None) -> str:
        """Create a raw text node from a string.

        Args:
            html: Raw text to insert

        Returns:
            A string containing the text.
        """
        text = NavigableString("" if html is None else str(html))

        # # Only append to parent if we're creating a new text node
        # # This prevents double-appending when the text is used in other operations
        if parent := current_tag_context.get():
            parent.append(text)

        # Return the raw string only when no parent (for direct usage)
        return text

    def raw(self, html: str | bytes, parser: str | None = None) -> Tag:
        """Create a Tag from a raw HTML string.

        Args:
            html: Raw HTML string to parse

        Returns:
            Tag: A new Tag object containing the parsed HTML
        """
        if isinstance(html, bytes):
            # Use charset-normalizer to detect the encoding and decode the bytes
            detected = from_bytes(html).best()

            if detected is None:
                raise UiEncodingError

            html = str(detected)  # Convert bytes to a string

        parser = parser or (
            self.__class__.get_xml_parser() if html.startswith("<?xml") else self.__class__.get_html_parser()
        )

        parsed = BeautifulSoup(html, parser)

        if parser == "lxml" and parsed.html:
            if body := parsed.html.body:
                parsed = body
            elif head := parsed.html.head:
                parsed = head

        # Count root elements
        root_elements = [child for child in parsed.children if isinstance(child, BeautifulSoupTag)]

        if len(root_elements) == 1:
            # Single root element - return it directly
            tag = Tag.from_existing_bs4tag(root_elements[0])
        else:
            # Multiple root elements or text only - handle as fragments
            tag = Tag(name="fragment")
            tag.string = ""

            if root_elements:
                # Add all root elements
                for child in root_elements:
                    tag.append(Tag.from_existing_bs4tag(child))
            else:
                # Text only content
                tag.string = html

            # Ensure fragment tag doesn't render
            tag.hidden = True

        if parent := current_tag_context.get():
            parent.append(tag)

        return tag

    def __getattr__(self, tag_name: str) -> Callable[..., Tag]:
        def create_tag(*args: Any, **kwargs: str | int | float | Sequence[Any]) -> Tag:
            # Convert underscore attributes to dashes
            converted_kwargs: dict[str, Any] = {}

            for key, value in kwargs.items():
                key = key.rstrip("_").replace("_", "-")

                if key == "class":
                    if isinstance(value, list | tuple):
                        value = " ".join(str(v) for v in value if isinstance(v, str | int | float))
                else:
                    # Handle boolean attributes
                    if isinstance(value, bool) and value:
                        value = None

                converted_kwargs[key] = value

            # Create a BeautifulSoupTag directly
            base_tag = BeautifulSoupTag(
                name=tag_name,
                attrs=converted_kwargs,
            )

            # Wrap it into our Tag class
            tag_obj = Tag.from_existing_bs4tag(base_tag)

            # Handle content
            if args:
                arg = args[0]
                if isinstance(arg, Tag):
                    tag_obj.append(arg)
                elif arg is None:
                    tag_obj.string = ""
                else:
                    tag_obj.string = str(arg)

            # If there's a current parent, append this tag to it
            if parent := current_tag_context.get():
                parent.append(tag_obj)

            return tag_obj

        return create_tag


ui = Ui()
