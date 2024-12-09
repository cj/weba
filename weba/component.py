from __future__ import annotations

from abc import ABC, ABCMeta
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar, cast, overload

from .context import current_parent
from .tag import Tag
from .ui import ui

if TYPE_CHECKING:
    from collections.abc import Callable


T = TypeVar("T", bound="Component")


class TagDecorator(Generic[T]):
    """Descriptor for tag-decorated methods."""

    def __init__(
        self,
        method: Callable[[T, Tag | None], Tag],
        selector: str | None = None,
        extract: bool = False,
        clear: bool = False,
    ):
        self.method = method
        self.selector = selector
        self.extract = extract
        self.clear = clear
        self._cache_name = f"_{method.__name__}_result"
        self.__name__ = method.__name__

    def __get__(self, instance: T | None, owner: type[T]) -> Tag:
        if instance is None:
            raise AttributeError(f"can't access attribute {self.__name__} on class")  # noqa: TRY003

        # Return cached result if it exists
        if hasattr(instance, self._cache_name):
            return getattr(instance, self._cache_name)

        # Find tag using selector if provided
        tag = None

        if self.selector:
            if self.selector.startswith("<!--"):
                tag = instance._root_tag.comment_one(self.selector)  # pyright: ignore[reportPrivateUsage]
            else:
                tag = instance._root_tag.select_one(self.selector)  # pyright: ignore[reportPrivateUsage]

        # Call method with found tag if it accepts two arguments, otherwise just call with self
        if self.method.__code__.co_argcount == 2:
            result = self.method(instance, tag)
        else:
            result = self.method(instance)  # pyright: ignore[reportCallIssue, reportUnknownVariableType]
            # If method returns None, return the found tag instead
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
def component_tag(selector: Callable[[T, Tag], Tag]) -> TagDecorator[T]: ...


@overload
def component_tag(
    selector: str,
    *,
    extract: bool = False,
    clear: bool = False,
) -> Callable[
    [Callable[[T, Tag], Any] | Callable[[T], Any]],
    TagDecorator[T],
]: ...


def component_tag(
    selector: str | Callable[[T, Tag], Any],
    *,
    extract: bool = False,
    clear: bool = False,
) -> TagDecorator[T] | Callable[[Callable[[T, Tag], Any]], TagDecorator[T]]:
    """Decorator factory for component tag methods.

    Args:
        selector: Either a CSS selector string or the decorated method
        extract: Whether to extract the matched tag
        clear: Whether to clear the matched tag

    Returns:
        Either a TagFunction directly (if called with method) or a decorator
    """
    # Handle case where decorator is used without parameters
    if callable(selector):
        method = selector

        Component._tag_methods.append(method.__name__)  # pyright: ignore[reportPrivateUsage]

        return TagDecorator(method)  # pyright: ignore[reportArgumentType]

    # Handle case where decorator is used with parameters
    def decorator(method: Callable[[T, Tag], Any]) -> TagDecorator[T]:
        Component._tag_methods.append(method.__name__)  # pyright: ignore[reportPrivateUsage]

        return TagDecorator(
            method,  # pyright: ignore[reportArgumentType]
            selector=selector,
            extract=extract,
            clear=clear,
        )

    return decorator


class ComponentMeta(ABCMeta):
    """Metaclass for Component to handle automatic rendering."""

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        return super().__call__(*args, **kwargs)


class Component(ABC, metaclass=ComponentMeta):
    """Base class for UI components."""

    html: ClassVar[str]
    _root_tag: Tag
    _tag_methods: ClassVar[list[Any]] = []

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        if not hasattr(cls, "html"):
            raise ValueError("Component must define 'html' class variable")  # noqa: TRY003

        html = cls.html

        if html.endswith(".html"):
            # Load from file
            path = Path(html)

            if not path.exists():
                raise FileNotFoundError(f"Template file not found: {html}")  # noqa: TRY003

            html = path.read_text()

        # Create component instance
        instance = super().__new__(cls)

        # Create and store the root tag
        root_tag = ui.raw(html)

        object.__setattr__(instance, "_root_tag", root_tag)

        # Initialize the instance
        instance.__init__(*args, **kwargs)

        # Add to current parent if exists
        parent = current_parent.get()

        if parent is not None:
            parent.add_child(root_tag)

        # Execute all tag-decorated methods before render
        if hasattr(cls, "_tag_methods"):
            for method_name in cls._tag_methods:
                getattr(instance, method_name)

        # Call render after initialization
        instance.render()

        return instance

    def render(self) -> None:
        """Override this method to customize component rendering."""
        pass

    def __str__(self) -> str:
        return str(self._root_tag)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the underlying Tag."""
        # First check if it's a tag method
        if name in self.__class__._tag_methods:
            for _key, value in self.__class__.__dict__.items():
                if isinstance(value, TagDecorator) and value.__name__ == name:
                    return value.__get__(self, self.__class__)  # pyright: ignore[reportUnknownMemberType]

        # Then check root tag
        if hasattr(self._root_tag, name):
            return getattr(self._root_tag, name)

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")  # noqa: TRY003

    def __setattr__(self, name: str, value: Any) -> None:
        """Handle attribute setting for both component and root tag."""

        if name == "_root_tag" or not hasattr(self._root_tag, name):
            object.__setattr__(self, name, value)
        else:
            setattr(self._root_tag, name, value)
