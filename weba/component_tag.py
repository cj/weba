from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from .tag_decorator import TagDecorator

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from .component import Component
    from .tag import Tag

T = TypeVar("T", bound="Component")  # pyright: ignore[reportUnknownVariableType]


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
