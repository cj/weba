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

    def __get__(self, instance: T | None, owner: type[T]):
        # Return cached result if it exists
        if response := getattr(instance, self._cache_name):
            return response

        # Find tag using selector if provided
        if self.selector.startswith("<!--"):
            # Strip HTML comment markers and whitespace
            stripped_selector = self.selector[4:-3].strip()
            tag = instance.comment_one(stripped_selector)  # type: ignore[attr-defined]
        else:
            tag = instance.select_one(self.selector)  # type: ignore[attr-defined]

        # Call the decorated method
        argcount = self.method.__code__.co_argcount  # type: ignore[attr-defined]

        result = cast(Tag, (self.method(instance, tag) if argcount == 2 else self.method(instance)) or tag)  # pyright: ignore[reportArgumentType, reportCallIssue]

        # Handle extraction and clearing if requested
        if self.extract:
            result.extract()

        if self.clear:
            result.clear()

        # Cache the result
        setattr(instance, self._cache_name, result)

        return result


@overload
def component_tag(selector: Callable[[T, Tag], str]) -> TagDecorator[T]: ...


@overload
def component_tag(
    selector: str,
    *,
    extract: bool = False,
    clear: bool = False,
) -> Callable[[Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None]], TagDecorator[T]]: ...


def component_tag(
    selector: Any,
    *,
    extract: bool = False,
    clear: bool = False,
) -> TagDecorator[T] | Callable[[Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None]], TagDecorator[T]]:
    """Decorator factory for component tag methods.

    Args:
        selector: Either a CSS selector string or the decorated method
        extract: Whether to extract the matched tag
        clear: Whether to clear the matched tag

    Returns:
        Either a TagDecorator directly (if called with method) or a decorator.
    """

    # Decorator used with parameters
    def decorator(method: Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None]) -> TagDecorator[T]:
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
    _tag_methods: ClassVar[list[str]]

    def __new__(cls, *args: Any, **kwargs: Any):
        html = cls.html

        if html.endswith(".html") or html.endswith(".svg") or html.endswith(".xml"):
            cls_path = inspect.getfile(cls)
            cls_dir = os.path.dirname(cls_path)
            path = Path(cls_dir, html)

            html = path.read_text()

        # Create root tag
        root_tag = ui.raw(html)

        # Create instance as a Tag with the root tag's properties
        instance = super().__new__(cls)

        Tag.__init__(
            instance,
            name=root_tag.name,
            attrs=root_tag.attrs,
            sourcepos=root_tag.sourcepos,
            previous=root_tag.previous,
        )

        # Initialize the instance first
        instance.__init__(*args, **kwargs)

        # Copy all contents while preserving context
        contents = list(root_tag.contents)  # Make a copy of contents

        for content in contents:
            instance.append(content)

        root_tag.decompose()

        # Add to current parent if exists
        parent = current_parent.get()

        if parent is not None:
            parent.append(instance)

        # Execute tag decorators after contents are copied
        for method_name in getattr(cls, "_tag_methods", []):
            getattr(instance, method_name)

        instance.render()

        return instance

    def render(self) -> None:
        """Override this method to customize component rendering."""
        pass

    def __init__(self):
        pass
