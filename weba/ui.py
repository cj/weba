from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup
from bs4 import Tag as BeautifulSoupTag

from .context import current_parent
from .tag import Tag

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Sequence


class Ui:
    """A factory class for creating UI elements using BeautifulSoup."""

    def __init__(self):
        self.soup = BeautifulSoup("", "html.parser")

    def text(self, html: str | int | float | Sequence[Any] | None) -> Tag:
        """Create a raw text node from a string.

        Args:
            html: Raw text to insert

        Returns:
            A NavigableString containing the text.
        """
        if html is None:
            html = ""

        text_node = self.soup.new_string(str(html))  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

        if parent := current_parent.get():
            # Append the text node directly to the parent
            parent.append(text_node)  # pyright: ignore[reportUnknownArgumentType]

        # Return the raw NavigableString node
        return text_node  # pyright: ignore[reportUnknownVariableType]

    def raw(self, html: str) -> Tag:
        """Create a Tag from a raw HTML string.

        Args:
            html: Raw HTML string to parse

        Returns:
            Tag: A new Tag object containing the parsed HTML
        """
        parsed = BeautifulSoup(html, "html.parser", preserve_whitespace_tags=["*"])

        if contents := parsed.contents:
            # Find the first Tag in parsed.contents
            for element in contents:
                if isinstance(element, BeautifulSoupTag):
                    # Wrap this existing BeautifulSoupTag in our Tag class
                    tag_obj = Tag.from_existing_bs4tag(element)

                    if parent := current_parent.get():
                        parent.append(tag_obj)

                    return tag_obj

            # If no tags found, treat as text
            return self.text(html)

        # If nothing parsed, fallback to text
        return self.text(html)

    def __getattr__(self, tag_name: str) -> Callable[..., Tag]:
        def create_tag(*args: Any, **kwargs: str | int | float | Sequence[Any]) -> Tag:
            # Convert underscore attributes to dashes
            converted_kwargs: dict[str, Any] = {}

            for key, value in kwargs.items():
                if key == "class_":
                    # class_ -> class
                    new_key = "class"
                    if isinstance(value, list | tuple):
                        value = " ".join(str(v) for v in value if isinstance(v, str | int | float))
                else:
                    new_key = key.replace("_", "-")
                    # Handle boolean attributes
                    if isinstance(value, bool) and value:
                        value = None

                converted_kwargs[new_key] = value

            # Remove trailing underscore from tag names like input_
            actual_tag_name = tag_name.rstrip("_")

            parent = current_parent.get()

            # Create a BeautifulSoupTag directly
            base_tag = BeautifulSoupTag(
                builder=self.soup.builder,
                name=actual_tag_name,
                attrs=converted_kwargs,
            )

            # Wrap it into our Tag class
            tag_obj = Tag.from_existing_bs4tag(base_tag)

            # If there's a current parent, append this tag to it
            if parent:
                parent.append(tag_obj)

            # Set string content if provided
            if args:
                # If the first argument is something renderable as string
                tag_obj.string = str(args[0])

            return tag_obj

        return create_tag


ui = Ui()
