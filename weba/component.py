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


@overload  # pragma: no cover NOTE: We have tests for these
def component_tag(selector: Callable[[T, Tag], str]) -> TagDecorator[T]: ...


@overload  # pragma: no cover
def component_tag(
    selector: str = "",
    *,
    extract: bool = False,
    clear: bool = False,
) -> Callable[[Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None]], TagDecorator[T]]: ...


def component_tag(
    selector: Any = "",
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

        # Create instance
        instance = super().__new__(cls)

        # Initialize the instance with root_tag's properties
        Tag.__init__(instance, name=root_tag.name, attrs=root_tag.attrs)

        # Move contents from root_tag to instance
        instance.extend(root_tag.contents)

        # Clean up root_tag
        root_tag.decompose()

        # Initialize the instance
        instance.__init__(*args, **kwargs)

        if parent := current_parent.get():
            parent.append(instance)

        # Execute tag decorators after contents are copied
        for method_name in getattr(cls, "_tag_methods", []):
            getattr(instance, method_name)

        # Call render if it's not asynchronous
        if not inspect.iscoroutinefunction(instance.render) and callable(instance.render):
            instance.render()

        return instance

    def __await__(self):
        async def _coro():
            if inspect.iscoroutinefunction(self.render):  # pragma: no cover NOTE: we have tests for this
                await self.render()

            return self

        return _coro().__await__()

    def __init__(self):
        pass
