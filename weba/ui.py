from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, cast

from bs4 import BeautifulSoup, NavigableString
from bs4 import Tag as BeautifulSoupTag
from charset_normalizer import from_bytes

from .tag import Tag, current_tag_context

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence

    from bs4 import SoupStrainer


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

    def _handle_lxml_parser(self, html: str, parsed: BeautifulSoupTag) -> Tag | BeautifulSoupTag:
        stripped_html = html.strip().lower()

        if parsed and parsed.html and all(tag in stripped_html for tag in ("<body", "<head", "<html")):
            return parsed
        elif (body := parsed.html) and (stripped_html.startswith("<body") or (body := body.body)):
            return body
        elif (head := parsed.html) and (stripped_html.startswith("<head") or (head := head.head)):
            return head

        return parsed

    def raw(self, html: str | bytes, parser: str | None = None, parse_only: SoupStrainer | None = None) -> Tag:
        """Create a Tag from a raw HTML string.

        Args:
            html: Raw HTML string to parse
            parser: Parser to use (defaults to XML or HTML parser based on content)
            parse_only: Optional SoupStrainer to limit parsing to specific tags

        Returns:
            Tag: A new Tag object containing the parsed HTML
        """
        if isinstance(html, bytes):
            html = str(from_bytes(html).best())

        parser = parser or (
            self.__class__.get_xml_parser() if html.startswith("<?xml") else self.__class__.get_html_parser()
        )

        parsed = BeautifulSoup(html, parser, parse_only=parse_only)

        # NOTE: This is to html lxml always wrapping in html > body tags
        if parser == "lxml":
            parsed = self._handle_lxml_parser(html, parsed)

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

    def _process_attribute_key(self, key: str) -> str:
        """Process attribute key by converting underscores to dashes."""
        return key.rstrip("_").replace("_", "-")

    def _process_class_attribute(self, value: Any) -> str:
        """Process class attribute values.

        Args:
            value: A list or tuple of class names

        Returns:
            A space-separated string of class names
        """
        # Try to iterate the values without making assumptions about the type
        try:
            # Use list comprehension to filter and convert valid values to strings
            result = " ".join(str(item) for item in value if isinstance(item, str | int | float))
        except Exception:
            # Fall back to string conversion if iteration fails
            result = str(value)

        return result

    def _process_attribute_value(self, key: str, value: Any) -> tuple[bool, Any]:
        """Process attribute value based on its type and key name.

        Returns:
            Tuple of (include_attribute, processed_value)
        """
        # Handle class attribute specially
        if key == "class" and isinstance(value, list | tuple):
            return True, self._process_class_attribute(value)

        # Handle boolean attributes
        if isinstance(value, bool):
            # Use conditional expression instead of if-else
            return (True, "") if value else (False, None)

        return True, value

    def __getattr__(self, tag_name: str) -> Callable[..., Tag]:  # noqa: C901
        def create_tag(*args: Any, **kwargs: str | int | float | Sequence[Any]) -> Tag:
            # Extract special class operations
            append_class = kwargs.pop("_append_class", None)
            prepend_class = kwargs.pop("_prepend_class", None)

            # Convert remaining attributes
            converted_kwargs: dict[str, Any] = {}

            for key, value in kwargs.items():
                processed_key = self._process_attribute_key(key)
                include, processed_value = self._process_attribute_value(processed_key, value)

                if include:
                    converted_kwargs[processed_key] = processed_value

            # Create and process tag
            base_tag = BeautifulSoupTag(name=tag_name, attrs=converted_kwargs)
            tag_obj = Tag.from_existing_bs4tag(base_tag)

            # Apply special class operations if specified
            if append_class is not None or prepend_class is not None:
                # Create a dictionary only with non-None values
                extra_kwargs = {}
                if append_class is not None:
                    extra_kwargs["_append_class"] = append_class
                if prepend_class is not None:
                    extra_kwargs["_prepend_class"] = prepend_class

                # Apply the attributes if we have any
                if extra_kwargs and hasattr(tag_obj, "with_attrs"):
                    # Need to handle type checking here
                    # We know this is safe because we checked with hasattr
                    with_attrs = tag_obj.with_attrs
                    # Cast to callable to make type checker happy
                    method = cast(Callable[..., Any], with_attrs)
                    method(**extra_kwargs)

            # Handle content from args
            if args and (arg := args[0]) is not None:
                tag_obj.string = "" if isinstance(arg, Tag) else str(arg)
                if isinstance(arg, Tag):
                    tag_obj.append(arg)

            # Append to parent if in context
            if parent := current_tag_context.get():
                parent.append(tag_obj)

            return tag_obj

        return create_tag


ui = Ui()
