from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, NavigableString
from bs4 import Tag as BeautifulSoupTag

from .tag import Tag, current_tag_context

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Sequence


class Ui:
    """A factory class for creating UI elements using BeautifulSoup."""

    def __init__(self):
        self.soup = BeautifulSoup("", "html.parser")

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

    def raw(self, html: str, parser: str | None = None) -> Tag:
        """Create a Tag from a raw HTML string.

        Args:
            html: Raw HTML string to parse

        Returns:
            Tag: A new Tag object containing the parsed HTML
        """
        parser = parser or ("xml" if html.startswith("<?xml") else "html.parser")

        parsed = BeautifulSoup(html, parser)

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

            parent = current_tag_context.get()

            # Create a BeautifulSoupTag directly
            base_tag = BeautifulSoupTag(
                builder=self.soup.builder,
                name=tag_name,
                attrs=converted_kwargs,
            )

            # Wrap it into our Tag class
            tag_obj = Tag.from_existing_bs4tag(base_tag)

            # If there's a current parent, append this tag to it
            if parent:
                parent.append(tag_obj)

            # Handle content
            if args:
                arg = args[0]
                if isinstance(arg, Tag):
                    tag_obj.append(arg)
                elif arg is None:
                    tag_obj.string = ""
                else:
                    tag_obj.string = str(arg)

            return tag_obj

        return create_tag


ui = Ui()
