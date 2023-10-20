import inspect
from typing import Any, Callable, Coroutine, Dict, ParamSpec, TypeVar

from .methods import Methods

P = ParamSpec("P")
R = TypeVar("R")


class NewInitCaller(type):
    def __call__(cls_, *args: Any, **kwargs: Any):  # type: ignore  # noqa: N804
        # sourcery skip: instance-method-first-arg-name
        """Called when you call MyNewClass()"""
        obj = type.__call__(cls_, *args, **kwargs)
        obj._args = args or ()
        obj._kwargs = kwargs or {}

        if len(inspect.signature(obj.__init__).parameters) > 0:
            obj.__init__(*args, **kwargs)

        if not obj._kwargs.get("_skip_content_call"):
            if hasattr(obj, "_content") and not inspect.iscoroutinefunction(obj._content):
                if len(inspect.signature(obj._content).parameters) > 0:
                    return obj._content(*args, **kwargs)
                else:
                    return obj._content()

            if hasattr(obj, "content") and not inspect.iscoroutinefunction(obj.content):
                if len(inspect.signature(obj.content).parameters) > 0:
                    return obj.content(*args, **kwargs)
                else:
                    return obj.content()

        return obj


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
        if hasattr(self, "_content_async") and inspect.iscoroutinefunction(self._content_async):
            # check to see if content takes args
            if len(inspect.signature(self._content_async).parameters) > 0:
                return self._content_async(*self._args, **self._kwargs).__await__()
            else:
                return self._content_async().__await__()

        if hasattr(self, "content_async") and inspect.iscoroutinefunction(self.content_async):
            # check to see if content takes args
            if len(inspect.signature(self.content_async).parameters) > 0:
                return self.content_async(*self._args, **self._kwargs).__await__()
            else:
                return self.content_async().__await__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        pass
