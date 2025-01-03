from __future__ import annotations

import inspect
import os
from abc import ABC, ABCMeta
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from .tag import Tag, current_tag_context
from .tag_decorator import TagDecorator
from .ui import ui

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

T = TypeVar("T", bound="Component")


@contextmanager
def no_tag_context():
    """Temporarily clear the current parent context."""
    parent = current_tag_context.get()
    current_tag_context.set(None)

    try:
        yield
    finally:
        current_tag_context.set(parent)


class ComponentAttributeError(AttributeError):
    """Raised when a component is missing required attributes."""

    def __init__(self, component: type[Component]) -> None:
        name = component.__name__
        super().__init__(f"Component ({name}): Must define 'src' class attribute")


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

    src: ClassVar[str | Callable[[], str]]
    """The HTML source template for the component. Can be inline HTML, a path to an HTML file, or a callable returning either."""
    src_parser: ClassVar[str] | None = None
    """The parser to use when parsing the source HTML. Defaults to 'html.parser'."""
    _tag_methods: ClassVar[list[str]]
    _called_with_context: bool
    _has_async_hooks: bool = False
    _doctype: str | None = None

    @classmethod
    def _get_source_content(cls) -> tuple[str, str | None]:
        """Get the source content and doctype."""
        src = getattr(cls, "src", None)

        if callable(src):
            with no_tag_context():
                src = src()

        if src is None or not isinstance(src, str):
            raise ComponentAttributeError(cls)

        if src.endswith(".html") or src.endswith(".svg") or src.endswith(".xml"):
            cls_path = inspect.getfile(cls)
            cls_dir = os.path.dirname(cls_path)
            path = Path(cls_dir, src)

            # Set XML parser for SVG and XML files if not explicitly set
            if not cls.src_parser and (src.endswith(".svg") or src.endswith(".xml")):
                cls.src_parser = "xml"

            src = path.read_text()

        doctype = src.split("\n", 1)[0]
        doctype = doctype if "!doctype" in doctype.lower() else None

        return src, doctype

    def _init_from_tag(self, root_tag: Tag) -> None:
        """Initialize component from a root tag."""
        Tag.__init__(self, name=root_tag.name, attrs=root_tag.attrs)
        self.extend(root_tag.contents)
        root_tag.decompose()

    def __new__(cls, *args: Any, **kwargs: Any):
        src, doctype = cls._get_source_content()
        root_tag = ui.raw(src, parser=cls.src_parser or "html.parser")

        instance = super().__new__(cls)
        instance._doctype = doctype
        instance._called_with_context = False

        instance._init_from_tag(root_tag)
        instance.__init__(*args, **kwargs)

        if parent := current_tag_context.get():
            parent.append(instance)

        instance._has_async_hooks = any(
            inspect.iscoroutinefunction(getattr(instance, hook, None))
            for hook in ["before_render", "render", "after_render"]
        )

        if not instance._has_async_hooks:
            instance._run_sync_hooks()

        return instance

    def _run_sync_hooks(self) -> None:
        """Run synchronous lifecycle hooks."""
        if callable(self.before_render):
            with no_tag_context():
                self.before_render()

        with no_tag_context():
            self._load_tag_methods()

        if callable(self.render):
            with no_tag_context():
                if response := self.render():
                    self._update_from_response(response)

        if callable(self.after_render):
            with no_tag_context():
                self.after_render()

    async def _async_render_hooks(self):
        if callable(self.before_render):
            with no_tag_context():
                await self.before_render() if inspect.iscoroutinefunction(self.before_render) else self.before_render()

        with no_tag_context():
            self._load_tag_methods()

        if callable(self.render):
            with no_tag_context():
                if response := await self.render() if inspect.iscoroutinefunction(self.render) else self.render():
                    self._update_from_response(response)

        if not self._called_with_context and callable(self.after_render):
            with no_tag_context():
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
        *args: Any,
    ) -> None:
        if callable(self.after_render):
            with no_tag_context():
                await self.after_render() if inspect.iscoroutinefunction(self.after_render) else self.after_render()

        return super().__exit__(*args)

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
