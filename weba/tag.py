from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Any

from bs4 import Tag as Bs4Tag

if TYPE_CHECKING:  # pragma: no cover
    from contextvars import Token

current_parent: ContextVar["Tag | None"] = ContextVar("current_parent", default=None)


class TagAttributeError(AttributeError):
    """Custom exception for missing attributes or methods in Tag objects."""

    def __init__(self, tag_name: str, attribute_name: str):
        self.tag_name = tag_name
        self.attribute_name = attribute_name
        super().__init__(self._generate_message())

    def _generate_message(self) -> str:
        return f"'{self.tag_name}' object has no attribute or method '{self.attribute_name}'"


class Tag:
    def __init__(self, tag: Bs4Tag, parent: "Tag | None" = None):
        self.tag = tag
        self.parent = parent
        self._children: list[Tag] = []
        self._token: Token[Tag | None] | None = None

    def __enter__(self) -> "Tag":
        self._token = current_parent.set(self)

        return self

    def __exit__(self, *args: Any) -> None:
        if self._token is not None:
            current_parent.reset(self._token)
        if self.parent and self not in self.parent._children:
            self.parent._children.append(self)

    def add_child(self, child: "Tag") -> None:
        """Add a child tag to this tag."""
        if child not in self._children:
            self._children.append(child)
            child.parent = self
            # Always ensure BS4 tag structure is correct
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

    def append(self, child: "Tag") -> None:
        """Append a child tag to this tag."""
        self.add_child(child)

    def wrap_tag(self, tag: Bs4Tag | None) -> "Tag | None":
        """Wrap a BeautifulSoup tag in a Tag instance."""
        if tag is None:
            return None

        # Check if the tag already has a parent Tag
        parent = self if tag.parent == self.tag else None

        return Tag(tag, parent)

    def __getattr__(self, name: str) -> Any:
        """Proxy any unknown attributes/methods to the underlying BeautifulSoup tag."""
        # Check if the attribute exists and is not None
        if hasattr(self.tag, name):
            attr = getattr(self.tag, name)

            # Ensure the attribute is callable or valid
            if attr is not None:
                if callable(attr):

                    def wrapped(*args: Any, **kwargs: Any) -> Any:
                        # Convert Tag instances to their underlying BeautifulSoup tags
                        converted_args = [arg.tag if isinstance(arg, Tag) else arg for arg in args]
                        converted_kwargs = {k: v.tag if isinstance(v, Tag) else v for k, v in kwargs.items()}
                        result = attr(*converted_args, **converted_kwargs)

                        # Wrap the result if it is a BeautifulSoup tag
                        if name in {"select_one", "find", "find_next", "find_previous"}:
                            return self.wrap_tag(result)  # pyright: ignore[reportArgumentType]
                        elif name in {"select", "find_all"}:
                            return [self.wrap_tag(t) for t in result if t is not None]  # pyright: ignore[reportGeneralTypeIssues, reportUnknownVariableType, reportUnknownArgumentType]

                        return result

                    return wrapped

                # If it's not callable, return the attribute value directly
                return attr if callable(attr) else attr

        # Attribute does not exist or is None
        raise TagAttributeError(type(self).__name__, name)

    def __str__(self) -> str:
        # Handle None content specially to render as empty string
        if self.tag.string == "None":
            self.tag.string = ""
        return str(self.tag)
