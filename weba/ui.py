from collections.abc import Callable, Sequence
from typing import Any

from bs4 import BeautifulSoup
from bs4 import Tag as BeautifulSoupTag

from .tag import Tag, current_parent


class Ui:
    """A factory class for creating UI elements using BeautifulSoup."""

    def __init__(self):
        self.soup = BeautifulSoup("", "html.parser")

    def __getattr__(self, tag_name: str) -> Callable[..., Tag]:
        def create_tag(*args: Any, **kwargs: str | int | float | Sequence[Any]) -> Tag:
            # Convert underscore attributes to dashes
            converted_kwargs: dict[str, Any] = {}

            for key, value in kwargs.items():
                # Special case for class_ attribute
                if key == "class_":
                    new_key = "class"
                    # Ensure value is a sequence
                    if isinstance(value, list | tuple):
                        value = " ".join(str(v) for v in value if isinstance(v, str | int | float))
                else:
                    new_key = key.replace("_", "-")
                    # Handle boolean attributes (like hx-boost)
                    if isinstance(value, bool) and value:
                        value = None

                converted_kwargs[new_key] = value

            # Special case for reserved python words like input_ to remove the underscore from the tag name
            actual_tag_name = tag_name.rstrip("_")

            parent = current_parent.get()

            # Create the tag directly using bs4.Tag
            tag = BeautifulSoupTag(
                builder=self.soup.builder,
                name=actual_tag_name,
                attrs=converted_kwargs,
            )

            # Create our wrapper Tag object
            tag_obj = Tag(tag, parent)

            # If there's a current parent, add this tag as its child
            if parent:
                parent.add_child(tag_obj)

            # Set string content if provided
            if args:
                tag.string = str(args[0])

            return tag_obj

        return create_tag


ui = Ui()
