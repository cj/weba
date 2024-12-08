import json
from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Any, cast

from bs4 import NavigableString
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


class TagKeyError(KeyError):
    """Custom exception for invalid key access in Tag objects."""

    def __init__(self, tag_type: str, key: str):
        self.tag_type = tag_type
        self.key = key
        super().__init__(self._generate_message())

    def _generate_message(self) -> str:
        return f"'{self.tag_type}' does not support attribute access: {self.key}"


class Tag:
    def __init__(self, tag: Bs4Tag, parent: "Tag | None" = None):
        # If it's a NavigableString, wrap it in a new Tag
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

        # NavigableString doesn't support item access
        if isinstance(self.tag, NavigableString):
            raise TagKeyError("NavigableString", key)

        if key != "class":
            value = self.tag[key]
            # Convert objects/arrays to JSON string representation
            return json.dumps(value) if isinstance(value, dict | list) else value

        # Initialize class as empty list if it doesn't exist
        if "class" not in self.tag.attrs:
            self.tag.attrs["class"] = []
            return cast(list[str], self.tag.attrs["class"])

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
        # Check if the attribute exists
        if not hasattr(self.tag, name):
            raise TagAttributeError(type(self).__name__, name)

        # Get the attribute
        attr = getattr(self.tag, name)

        # Check if the attribute is None
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

    def comment(self, selector: str) -> list["Tag"]:
        """Find all tags or text nodes that follow comments matching the given selector.

        Args:
            selector: The comment text to search for (e.g., "#button" or ".card")

        Returns:
            A list of Tag objects that immediately follow matching comments.
        """
        results: list[Tag] = []

        # Find all comment nodes matching the selector
        comments = self.tag.find_all(string=lambda text: isinstance(text, str) and selector in text.strip())

        for comment in comments:
            # Get the next sibling of the comment
            next_node = comment.next_sibling

            while next_node and isinstance(next_node, NavigableString) and not next_node.strip():
                next_node = next_node.next_sibling

            if next_node:
                if isinstance(next_node, Bs4Tag):
                    results.append(Tag(next_node))
                elif isinstance(next_node, NavigableString):
                    text = next_node.strip()
                    if text:
                        results.append(Tag(NavigableString(text)))  # pyright: ignore[reportArgumentType]

        return results

    def comment_one(self, selector: str) -> "Tag | None":
        """Find the first tag or text node that follows a comment matching the given selector.

        Args:
            selector: The comment text to search for (e.g., "#button" or ".card")

        Returns:
            The first Tag object that immediately follows a matching comment, or None if not found.
        """

        # Find all comment nodes matching the selector
        comments = self.tag.find_all(string=lambda text: isinstance(text, str) and selector in text.strip())

        for comment in comments:
            # Get the next sibling of the comment
            next_node = comment.next_sibling  # Includes all sibling nodes, not just tags

            while next_node:  # Iterate over siblings until a valid node is found
                if isinstance(next_node, Bs4Tag):
                    return Tag(next_node)

                # Wrap plain text nodes and return
                text = next_node.strip()

                if text:  # Only create node if non-empty after stripping
                    text_node = NavigableString(text)

                    return Tag(text_node)  # pyright: ignore[reportArgumentType]

                next_node = next_node.next_sibling  # Move to the next sibling

        return None

    def __str__(self) -> str:
        # Handle None content specially to render as empty string
        if not isinstance(self.tag, NavigableString) and self.tag.string == "None":
            self.tag.string = ""

        return str(self.tag)
