import inspect
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar, Dict

from .methods import Methods

P = ParamSpec("P")
R = TypeVar("R")


class NewInitCaller(type):
    def __call__(cls_, *args: Any, **kwargs: Any):  # type: ignore  # noqa: N804
        # sourcery skip: instance-method-first-arg-name
        """Called when you call MyNewClass()"""
        obj = type.__call__(cls_)
        obj._args = args or ()
        obj._kwargs = kwargs or {}

        if len(inspect.signature(obj.__init__).parameters) > 0:
            obj.__init__(*args, **kwargs)

        if hasattr(obj, "_content") and not inspect.iscoroutinefunction(obj._content):
            if len(inspect.signature(obj._content).parameters) > 0:
                return obj._content(*args, **kwargs)
            else:
                return obj._content(*args, **kwargs)

        if hasattr(obj, "content") and not inspect.iscoroutinefunction(obj.content):
            if len(inspect.signature(obj.content).parameters) > 0:
                return obj.content(*args, **kwargs)
            else:
                return obj.content()

        return obj


class Component(Methods, object, metaclass=NewInitCaller):
    content: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]
    _content: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]
    _args: tuple[Any, ...]
    _kwargs: Dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __await__(self) -> Any:
        if hasattr(self, "_content") and inspect.iscoroutinefunction(self._content):
            # check to see if content takes args
            if len(inspect.signature(self._content).parameters) > 0:
                return self._content(*self._args, **self._kwargs).__await__()
            else:
                return self._content().__await__()

        if hasattr(self, "content") and inspect.iscoroutinefunction(self.content):
            # check to see if content takes args
            if len(inspect.signature(self.content).parameters) > 0:
                return self.content(*self._args, **self._kwargs).__await__()
            else:
                return self.content().__await__()
                return self.content().__await__()
