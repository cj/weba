from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, cast

from .tag import Tag

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from .component import Component

T = TypeVar("T", bound="Component")


class TagDecorator(Generic[T]):
    """Descriptor for tag-decorated methods."""

    def __init__(
        self,
        method: Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None],
        selector: str,
        extract: bool = False,
        clear: bool = False,
    ) -> None:
        self.method = method
        self.selector = selector
        self.extract = extract
        self.clear = clear
        self._cache_name = f"_{method.__name__}_result"
        self.__name__ = method.__name__

    def __get__(self, instance: T, owner: type[T]):
        # Return cached result if it exists
        if response := getattr(instance, self._cache_name):
            return response

        if not self.selector:
            tag = instance
        # Find tag using selector if provided
        elif self.selector.startswith("<!--"):
            # Strip HTML comment markers and whitespace
            stripped_selector = self.selector[4:-3].strip()
            tag = instance.comment_one(stripped_selector)  # type: ignore[attr-defined]
        else:
            tag = instance.select_one(self.selector)  # type: ignore[attr-defined]

        # Call the decorated method
        argcount = self.method.__code__.co_argcount  # type: ignore[attr-defined]

        # Handle extraction and clearing if requested
        if self.extract and tag is not None:
            tag.extract()

        if isinstance(tag, Tag) and self.clear:
            tag.clear()

        result = cast(Tag, (self.method(instance, tag) if argcount == 2 else self.method(instance)) or tag)  # pyright: ignore[reportArgumentType, reportCallIssue]

        # Cache the result
        setattr(instance, self._cache_name, result)

        return result
