from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from .component import Component
    from .tag import Tag

T = TypeVar("T", bound="Component")


class TagNotFoundError(RuntimeError):
    """Raised when a @tag can't find the selector."""

    def __init__(self, selector: str, fn_name: str, component: type[Component]) -> None:
        super().__init__(f"{component.__name__}.{fn_name} did not find selector: {selector}.")


class TagDecorator(Generic[T]):
    """Descriptor for tag-decorated methods."""

    def __init__(
        self,
        method: Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None],
        selector: str,
        extract: bool = False,
        clear: bool = False,
        root_tag: bool = False,
    ) -> None:
        self.method = method
        self.selector = selector
        self.extract = extract
        self.clear = clear
        self.root_tag = root_tag
        self.__name__ = method.__name__

    def __set__(self, instance: T, value: Tag):
        getattr(instance, self.method.__name__).replace_with(value)
        instance._cached_tags[self.__name__] = value  # pyright: ignore[reportPrivateUsage]

    def __get__(self, instance: T, owner: type[T]):
        # Return cached result if it exists
        if response := instance._cached_tags.get(self.__name__):  # pyright: ignore[reportPrivateUsage]
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

        if not tag:
            raise TagNotFoundError(self.selector, self.__name__, owner)

        if self.clear:
            tag.clear()

        # Handle extraction and clearing if requested
        if self.extract and tag:
            tag.extract()

        # Call the decorated method
        argcount = self.method.__code__.co_argcount  # type: ignore[attr-defined]
        method_result = self.method(instance, tag) if argcount == 2 else self.method(instance)  # pyright: ignore[reportArgumentType, reportCallIssue]

        # If method returns a value directly without needing the tag, use that
        if method_result is not None:
            if tag and tag != instance:
                tag.replace_with(method_result)

            tag = method_result

        result = tag

        # Handle root tag replacement if requested
        if self.root_tag:
            result = instance.replace_root_tag(result.copy())

        # Cache the result
        instance._cached_tags[self.__name__] = result  # pyright: ignore[reportPrivateUsage]

        return result
