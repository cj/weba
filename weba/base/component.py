import inspect
from typing import Any, Callable, Coroutine, Dict

from .methods import Methods


@staticmethod
def _is_coroutine(obj: Any, method_name: str) -> bool:
    """Check if a method exists and is a coroutine"""
    method = getattr(obj, method_name, None)
    return bool(method and inspect.iscoroutinefunction(method))


class NewInitCaller(type):
    def __call__(self, *args: Any, **kwargs: Any):  # type: ignore  # noqa: N804
        """Called when you call MyNewClass()"""
        obj = type.__call__(self, *args, **kwargs)
        obj._args = args or ()
        obj._kwargs = kwargs or {}

        init_signature = inspect.signature(obj.__init__)
        if len(init_signature.parameters) > 0:
            obj.__init__(*args, **kwargs)

        if not obj._kwargs.get("_skip_content_call"):
            for method_name in ["_content", "content"]:
                if self._is_callable(obj, method_name):
                    method = getattr(obj, method_name)
                    method_signature = inspect.signature(method)
                    return method(*args, **kwargs) if len(method_signature.parameters) > 0 else method()
        return obj

    @staticmethod
    def _is_callable(obj: Any, method_name: str) -> bool:
        """Check if a method exists and is not a coroutine"""
        method = getattr(obj, method_name, None)
        return bool(method and not inspect.iscoroutinefunction(method))


class Component(Methods, object, metaclass=NewInitCaller):
    content: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]
    content_async: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]
    _content: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]
    _content_async: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]
    _args: tuple[Any, ...]
    _kwargs: Dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __await__(self) -> Any:
        for method_name in ["_content", "content", "_content_async", "content_async"]:
            method = getattr(self, method_name)
            method_signature = inspect.signature(method)
            return (
                method(*self._args, **self._kwargs).__await__()
                if len(method_signature.parameters) > 0
                else method().__await__()
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        pass

    def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        pass
