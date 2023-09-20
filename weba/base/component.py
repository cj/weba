import inspect
from typing import Any, Callable, Coroutine, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class NewInitCaller(type):
    def __call__(cls_, *args: Any, **kwargs: Any):  # type: ignore  # noqa: N804
        # sourcery skip: instance-method-first-arg-name
        """Called when you call MyNewClass()"""
        obj = type.__call__(cls_, *args, **kwargs)
        obj.__init__(*args, **kwargs)

        if hasattr(obj, "content") and not inspect.iscoroutinefunction(obj.content):
            return obj.content(*args, **kwargs)

        return obj


class Component(object, metaclass=NewInitCaller):
    content: Optional[Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]]

    def __init__(self, *args: Any, **kwargs: Any):
        self._args = args
        self._kwargs = kwargs

    def __await__(self) -> Any:
        if hasattr(self, "content") and inspect.iscoroutinefunction(self.content):
            return self.content(*self._args, **self._kwargs).__await__()
