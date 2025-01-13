from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from .component import Component

T = TypeVar("T", bound="Component")


class ComponentSrcRequiredError(AttributeError):
    """Raised when a component is missing required attributes."""

    def __init__(self, component: type[Component]) -> None:
        name = component.__name__
        super().__init__(
            f"Component ({name}): Must define 'src' class attribute or have a render method which returns a Tag"
        )


class ComponentSrcTypeError(AttributeError):
    """Raised when a component src is not a str, method or Tag."""

    def __init__(self, component: type[Component]) -> None:
        name = component.__name__
        super().__init__(f"Component ({name}): 'src' must be either a str, callable[..., str | Tag] or Tag")


class ComponentSrcFileNotFoundError(FileNotFoundError):
    """Raised when a component's src file cannot be found."""

    def __init__(self, component: type[Component], filepath: str) -> None:
        name = component.__name__
        super().__init__(f"Component ({name}): Source file not found: {filepath}")


class ComponentSrcRootTagNotFoundError(AttributeError):
    """Raised when src_root_tag selector doesn't match any elements."""

    def __init__(self, component: type[Component], selector: str) -> None:
        name = component.__name__
        super().__init__(f"Component ({name}): src_root_tag selector '{selector}' not found in source HTML")


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


class ComponentTagNotFoundError(RuntimeError):
    """Raised when a @tag can't find the selector."""

    def __init__(self, selector: str, fn_name: str, component: type[Component]) -> None:
        super().__init__(f"{component.__name__}.{fn_name} did not find selector: {selector}.")
