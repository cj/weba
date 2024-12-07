from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from .tag import Tag, current_parent

if TYPE_CHECKING:
    from bs4 import Tag as Bs4Tag


class Ui:
    """A factory class for creating UI elements using BeautifulSoup."""

    def __init__(self):
        self.soup = BeautifulSoup("", "html.parser")

    def __getattr__(self, tag_name: str) -> Callable[..., Tag]:
        def create_tag(*args: Any, **kwargs: str | int | float | Sequence[Any]) -> Tag:
            # Convert underscore attributes to dashes
            converted_kwargs = {}

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

            # Type ignore needed since BeautifulSoup's new_tag has complex typing
            tag: Bs4Tag = self.soup.new_tag(tag_name, **converted_kwargs)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]

            parent = current_parent.get()
            tag_obj = Tag(tag, parent)

            if args:
                tag.string = str(args[0])

            # If there's a current parent, add this tag as its child
            if parent:
                parent.add_child(tag_obj)

            return tag_obj

        return create_tag


ui = Ui()
