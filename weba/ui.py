from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from .tag import Tag, current_parent

if TYPE_CHECKING:
    from bs4 import Tag as Bs4Tag


class UiFactory:
    """A factory class for creating UI elements using BeautifulSoup."""

    def __init__(self):
        self.soup = BeautifulSoup("", "html.parser")

    def __getattr__(self, tag_name: str) -> Callable[..., Tag]:
        def create_tag(*args: Any, **kwargs: Any) -> Tag:
            tag: Bs4Tag = self.soup.new_tag(tag_name, **kwargs)  # pyright: ignore[reportUnknownMemberType]

            parent = current_parent.get()
            tag_obj = Tag(tag, parent)

            if args and isinstance(args[0], str):
                tag.string = str(args[0])

            # If there's a current parent, add this tag as its child
            if parent:
                parent.add_child(tag_obj)

            return tag_obj

        return create_tag


ui = UiFactory()
