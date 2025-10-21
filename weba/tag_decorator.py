from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, cast

from .errors import ComponentTagNotFoundError

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from .component import Component
    from .tag import Tag

T = TypeVar("T", bound="Component")


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
        """Set the tag value, replacing the old tag with the new one.

        This descriptor method enables assignment syntax for component tags:
            component.my_tag = new_tag

        The old tag is replaced in the DOM tree and the cache is updated.

        Args:
            instance: The component instance owning this tag
            value: The new Tag to replace the old one with
        """
        getattr(instance, self.method.__name__).replace_with(value)
        instance._cached_tags[self.__name__] = value  # pyright: ignore[reportPrivateUsage]

    def __get__(self, instance: T, owner: type[T]) -> Tag:
        """Get the tag, executing the decorated method if needed.

        This descriptor implements the @tag decorator functionality. It:
        1. Returns cached result if available
        2. Finds the tag using the selector (CSS or comment-based)
        3. Optionally clears or extracts the tag
        4. Executes the decorated method with the found tag
        5. Caches and returns the result

        The selector can be:
        - CSS selector: ".class" or "#id" or "div.container"
        - Comment selector: "<!-- #my-tag -->" for comment-based targeting
        - Empty string: uses the component instance itself

        Args:
            instance: The component instance to search within
            owner: The component class type

        Returns:
            The found and processed Tag

        Raises:
            ComponentTagNotFoundError: If the selector doesn't match any tag
        """
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
            raise ComponentTagNotFoundError(self.selector, self.__name__, owner)

        if self.clear:
            tag.clear()

        # Handle extraction and clearing if requested
        if self.extract and tag:
            tag.extract()

        # Call the decorated method
        argcount = self.method.__code__.co_argcount  # type: ignore[attr-defined]
        method_result = cast("Tag | None", self.method(instance, tag) if argcount == 2 else self.method(instance))  # pyright: ignore[reportArgumentType, reportCallIssue]

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
