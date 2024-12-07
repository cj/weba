from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Any

from bs4 import Tag as Bs4Tag

if TYPE_CHECKING:
    from contextvars import Token

current_parent: ContextVar["Tag | None"] = ContextVar("current_parent", default=None)


class Tag:
    def __init__(self, tag: Bs4Tag, parent: "Tag | None" = None):
        self.tag = tag
        self.parent = parent
        self._children: list[Tag] = []

    def __enter__(self) -> "Tag":
        self._token: Token[Tag | None] = current_parent.set(self)
        return self

    def __exit__(self, *args: Any) -> None:
        current_parent.reset(self._token)
        if self.parent:
            self.parent._children.append(self)

    def add_child(self, child: "Tag") -> None:
        """Add a child tag to this tag."""
        self._children.append(child)

    def __str__(self) -> str:
        # Clear any existing children to avoid duplicates
        self.tag.clear()

        # Add all children's tags
        for child in self._children:
            self.tag.append(child.tag)

        return str(self.tag)
