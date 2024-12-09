from __future__ import annotations

import inspect
import os
from abc import ABC, ABCMeta
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    TypeVar,
    cast,
    overload,
)

from .context import current_parent
from .tag import Tag
from .ui import ui

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

T = TypeVar("T", bound="Component")


class TagDecorator(Generic[T]):
    """Descriptor for tag-decorated methods."""

    def __init__(
        self,
        method: Callable[[T, Tag], Tag | None] | Callable[[T], Tag | None],
        selector: str | None = None,
        extract: bool = False,
        clear: bool = False,
    ) -> None:
        self.method = method
        self.selector = selector
        self.extract = extract
        self.clear = clear
        self._cache_name = f"_{method.__name__}_result"
        self.__name__ = method.__name__

    def __get__(self, instance: T | None, owner: type[T]) -> Tag:
        # Return cached result if it exists
        if response := getattr(instance, self._cache_name):
            return response

        # Find tag using selector if provided
        tag: Tag | None = None

        if self.selector:
            if self.selector.startswith("<!--"):
                # Strip HTML comment markers and whitespace
                stripped_selector = self.selector[4:-3].strip()
                tag = instance._root_tag.comment_one(stripped_selector)  # type: ignore[attr-defined]
            else:
                tag = instance._root_tag.select_one(self.selector)  # type: ignore[attr-defined]

        # Call the decorated method
        argcount = self.method.__code__.co_argcount  # type: ignore[attr-defined]

        if argcount == 2:
            # Method expects (self, tag)
            result = self.method(instance, tag)  # pyright: ignore[reportArgumentType, reportCallIssue]
        else:
            # Method expects only self
            result = self.method(instance)  # pyright: ignore[reportCallIssue, reportArgumentType]
            # If method returns None, use the found tag
            if result is None:
                result = tag

        # Handle extraction and clearing if requested
        if tag and self.extract:
            tag.extract()

        if tag and self.clear:
            tag.clear()

        # Cache the result
        setattr(instance, self._cache_name, result)

        return cast(Tag, result)


@overload
def component_tag(selector: Callable[[T, Tag], Tag | None]) -> TagDecorator[T]: ...


@overload
def component_tag(
    selector: str,
    *,
    extract: bool = False,
    clear: bool = False,
) -> Callable[[Callable[[T, Tag], Tag | None] | Callable[[T], Tag | None]], TagDecorator[T]]: ...


def component_tag(
    selector: str | Callable[[T, Tag], Tag | None],
    *,
    extract: bool = False,
    clear: bool = False,
) -> TagDecorator[T] | Callable[[Callable[[T, Tag], Tag | None] | Callable[[T], Tag | None]], TagDecorator[T]]:
    """Decorator factory for component tag methods.

    Args:
        selector: Either a CSS selector string or the decorated method
        extract: Whether to extract the matched tag
        clear: Whether to clear the matched tag

    Returns:
        Either a TagDecorator directly (if called with method) or a decorator.
    """

    if callable(selector):
        # Decorator used without parameters directly on the method
        method = selector

        return TagDecorator(method)

    # Decorator used with parameters
    def decorator(method: Callable[[T, Tag], Tag | None] | Callable[[T], Tag | None]) -> TagDecorator[T]:
        return TagDecorator(
            method,
            selector=selector,
            extract=extract,
            clear=clear,
        )

    return decorator


class ComponentMeta(ABCMeta):
    """Metaclass for Component to handle automatic rendering."""

    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type:
        cls = super().__new__(cls, name, bases, namespace)

        tag_methods: list[str] = [
            attr_value.__name__ for attr_value in namespace.values() if isinstance(attr_value, TagDecorator)
        ]
        cls._tag_methods = tag_methods  # pyright: ignore[reportAttributeAccessIssue]

        return cls

    def __call__(cls, *args: Any, **kwargs: Any):
        return super().__call__(*args, **kwargs)


class Component(ABC, Tag, metaclass=ComponentMeta):
    """Base class for UI components."""

    html: ClassVar[str]
    _root_tag: Tag
    _tag_methods: ClassVar[list[str]]

    def __new__(cls, *args: Any, **kwargs: Any) -> Component:
        html = cls.html

        if html.endswith(".html") or html.endswith(".svg") or html.endswith(".xml"):
            cls_path = inspect.getfile(cls)
            cls_dir = os.path.dirname(cls_path)
            path = Path(cls_dir, html)

            html = path.read_text()

        instance = super().__new__(cls)

        root_tag = ui.raw(html)

        object.__setattr__(instance, "_root_tag", root_tag)

        instance.__init__(*args, **kwargs)

        # Add to current parent if exists
        parent = current_parent.get()

        if parent is not None:
            parent.append(root_tag)

        # Execute all tag-decorated methods before render
        for method_name in getattr(cls, "_tag_methods", []):
            getattr(instance, method_name)

        instance.render()

        return instance

    def render(self) -> None:
        """Override this method to customize component rendering."""
        pass

    def __str__(self) -> str:
        return str(self._root_tag)

    def __getattr__(self, name: str):
        return getattr(self._root_tag, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._root_tag, name, value)
