from __future__ import annotations

import inspect
import os
from abc import ABC, ABCMeta
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from .context import current_parent
from .tag import Tag
from .tag_decorator import TagDecorator
from .ui import ui

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

T = TypeVar("T", bound="Component")


class ComponentTypeError(TypeError):
    """Raised when a component receives an invalid type."""

    def __init__(self, received_type: Any, component: type[Component]) -> None:
        name = component.__name__
        super().__init__(f"Component ({name}): Expected Tag, got {type(received_type)}")


class ComponentAfterRenderError(RuntimeError):
    """Raised when after_render is called in a synchronous context."""

    def __init__(self, component: type[Component]) -> None:
        name = component.__name__
        super().__init__(
            f"Component ({name}): after_render cannot be called in a synchronous context manager. "
            "Either make the context manager async or remove after_render."
        )


class ComponentAsyncError(RuntimeError):
    """Raised when async component is called synchronously."""

    def __init__(self, component: type[Component]) -> None:
        name = component.__name__
        super().__init__(
            f"Component ({name}): has async hooks but was called synchronously. "
            "Use 'await component' or 'async with component' instead."
        )


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
    _has_async_hooks: bool = False
    _doctype: str | None = None

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

        doctype = html.split("\n", 1)[0]

        # Handle doctype
        if "!doctype" in doctype.lower():
            instance._doctype = doctype

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
        instance._has_async_hooks = any(
            inspect.iscoroutinefunction(getattr(instance, hook, None))
            for hook in ["before_render", "render", "after_render"]
        )

        # For non-async components, run hooks immediately
        if not instance._has_async_hooks:
            if callable(instance.before_render):
                instance.before_render()

            instance._load_tag_methods()

            if callable(instance.render) and (response := instance.render()):
                instance._update_from_response(response)

            if callable(instance.after_render):
                instance.after_render()

        return instance

    async def _async_render_hooks(self):
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

    def __await__(self):
        return self._async_render_hooks().__await__()

    def __enter__(self):
        if self._has_async_hooks:
            raise ComponentAsyncError(self.__class__)

        if (
            hasattr(self, "after_render")
            and callable(self.after_render)
            and not inspect.iscoroutinefunction(self.after_render)
        ):
            raise ComponentAfterRenderError(self.__class__)

        self._called_with_context = True

        return super().__enter__()

    async def __aenter__(self):
        self._called_with_context = True

        await self._async_render_hooks()

        return super().__enter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if callable(self.after_render):
            await self.after_render() if inspect.iscoroutinefunction(self.after_render) else self.after_render()

        return super().__exit__()

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
            raise ComponentTypeError(response, self.__class__)

        if response == self:
            response = response.copy()

        self.clear()
        self.extend(response.contents)
        self.name = response.name
        self.attrs = response.attrs

    def __str__(self) -> str:
        if self._doctype:
            return f"{self._doctype}\n{super().__str__()}"

        return super().__str__()
