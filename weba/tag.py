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
        if self.parent and self not in self.parent._children:
            self.parent._children.append(self)

    def add_child(self, child: "Tag") -> None:
        """Add a child tag to this tag."""
        if child not in self._children:
            self._children.append(child)
            self.tag.append(child.tag)

    def __getitem__(self, key: str) -> Any:
        """Allow accessing tag attributes like tag['class']."""
        if key != "class":
            return self.tag[key]

        # Initialize class as empty list if it doesn't exist
        if "class" not in self.tag.attrs:
            self.tag.attrs["class"] = []
            return self.tag.attrs["class"]

        # Get the current value
        current_value = self.tag.attrs.get("class", [])

        # Convert string class to list if needed
        if isinstance(current_value, str):
            self.tag.attrs["class"] = current_value.split()
        elif not isinstance(current_value, list):
            self.tag.attrs["class"] = []

        return self.tag.attrs["class"]

    def __str__(self) -> str:
        # Store the original string content if it exists
        original_string = self.tag.string

        # Clear existing content
        self.tag.clear()

        # Add all children's tags first
        for child in self._children:
            self.tag.append(child.tag)

        # Restore the original string content if there were no children
        if not self._children and original_string is not None:
            self.tag.string = original_string

        return str(self.tag)
