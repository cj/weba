from __future__ import annotations

import inspect
import os
from abc import ABC, ABCMeta
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, overload

from .context import current_parent
from .tag import Tag
from .tag_decorator import TagDecorator
from .ui import ui


class ComponentTypeError(TypeError):
    """Raised when a component receives an invalid type."""

    def __init__(self, received_type: Any) -> None:
        super().__init__(f"Expected Tag, got {type(received_type)}")


if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

T = TypeVar("T", bound="Component")


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
        if not inspect.iscoroutinefunction(instance.render) and callable(instance.render):  # noqa: SIM102
            if response := instance.render():
                instance._update_from_response(response)

        return instance

    def __await__(self):
        async def _coro():
            if inspect.iscoroutinefunction(  # noqa: SIM102
                self.render
            ):  # pragma: no cover NOTE: we have tests for this
                if response := await self.render():
                    self._update_from_response(response)

            return self

        return _coro().__await__()

    def __init__(self):
        pass

    def _update_from_response(self, response: Any) -> None:
        """Update this component's content and attributes from a response tag.

        Args:
            response: The tag to copy content and attributes from
        """
        if not isinstance(response, Tag):
            raise ComponentTypeError(response)

        self.clear()
        self.extend(response.contents)
        self.name = response.name
        self.attrs = response.attrs
