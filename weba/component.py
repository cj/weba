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

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from types import TracebackType

T = TypeVar("T", bound="Component")


class ComponentTypeError(TypeError):
    """Raised when a component receives an invalid type."""

    def __init__(self, received_type: Any) -> None:
        super().__init__(f"Expected Tag, got {type(received_type)}")


class ComponentAfterRenderError(RuntimeError):
    """Raised when after_render is called in a synchronous context."""

    def __init__(self) -> None:
        super().__init__(
            "after_render cannot be called in a synchronous context manager. "
            "Either make the context manager async or remove after_render."
        )


@overload  # pragma: no cover NOTE: We have tests for these
def component_tag(
    selector_or_method: Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None],
) -> TagDecorator[T]: ...


@overload  # pragma: no cover
def component_tag(
    selector_or_method: str = "",
    *,
    extract: bool = False,
    clear: bool = False,
) -> Callable[[Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None]], TagDecorator[T]]: ...


def component_tag(
    selector_or_method: str | Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None] = "",
    *,
    extract: bool = False,
    clear: bool = False,
) -> TagDecorator[T] | Callable[[Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None]], TagDecorator[T]]:
    """Decorator factory for component tag methods.

    Args:
        selector_or_method: Either a CSS selector string, or the decorated method directly
        extract: Whether to extract the matched tag
        clear: Whether to clear the matched tag

    Returns:
        Either a TagDecorator directly (if called with method) or a decorator.
    """
    if callable(selector_or_method):
        # Decorator used without parameters
        return TagDecorator(selector_or_method, selector="", extract=False, clear=False)

    # Decorator used with parameters
    def decorator(method: Callable[[T, Tag], Tag | T | None] | Callable[[T], Tag | T | None]) -> TagDecorator[T]:
        return TagDecorator(
            method,
            selector=str(selector_or_method),
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

    # NOTE: This prevents the default __init__ method from being called
    def __call__(cls, *args: Any, **kwargs: Any):
        # sourcery skip: instance-method-first-arg-name
        return cls.__new__(cls, *args, **kwargs)  # pyright: ignore[reportArgumentType]


class Component(ABC, Tag, metaclass=ComponentMeta):
    """Base class for UI components."""

    html: ClassVar[str]
    _tag_methods: ClassVar[list[str]]
    _called_with_context: bool

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

        instance._called_with_context = False

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

        # Check if any hooks are async
        has_async_hooks = any(
            inspect.iscoroutinefunction(getattr(instance, hook, None))
            for hook in ["before_render", "render", "after_render"]
        )

        # Call render if it's not asynchronous
        if not has_async_hooks:
            if callable(instance.before_render):
                instance.before_render()

            instance._load_tag_methods()

            if callable(instance.render) and (response := instance.render()):
                instance._update_from_response(response)

            if callable(instance.after_render):
                instance.after_render()

        return instance

    def __await__(self):
        async def _coro():
            if callable(self.before_render):
                await self.before_render() if inspect.iscoroutinefunction(self.before_render) else self.before_render()

            self._load_tag_methods()

            if callable(self.render) and (
                response := await self.render() if inspect.iscoroutinefunction(self.render) else self.render()
            ):
                self._update_from_response(response)

            if not self._called_with_context and callable(self.after_render):
                await self.after_render() if inspect.iscoroutinefunction(self.after_render) else self.after_render()

            return self

        return _coro().__await__()

    def __enter__(self):
        if (
            hasattr(self, "after_render")
            and callable(self.after_render)
            and not inspect.iscoroutinefunction(self.after_render)
        ):
            raise ComponentAfterRenderError()

        return super().__enter__()

    async def __aenter__(self):
        self._called_with_context = True

        await self
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if callable(self.after_render):
            await self.after_render() if inspect.iscoroutinefunction(self.after_render) else self.after_render()

        return None

    def _load_tag_methods(self) -> None:
        # Execute tag decorators after contents are copied
        for method_name in getattr(self.__class__, "_tag_methods", []):
            getattr(self, method_name)

    def __init__(self):
        pass

    def _update_from_response(self, response: Any) -> None:
        """Update this component's content and attributes from a response tag.

        Args:
            response: The tag to copy content and attributes from
        """
        if not isinstance(response, Tag):
            raise ComponentTypeError(response)

        if response == self:
            response = response.copy()

        self.clear()
        self.extend(response.contents)
        self.name = response.name
        self.attrs = response.attrs
