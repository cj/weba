import inspect
from typing import Any, Callable, Coroutine, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class NewInitCaller(type):
    def __call__(cls, *args: Any, **kwargs: Any):  # type: ignore
        # sourcery skip: instance-method-first-arg-name
        """Called when you call MyNewClass()"""
        obj = type.__call__(cls, *args, **kwargs)
        obj.__init__(*args, **kwargs)

        if hasattr(obj, "content") and not inspect.iscoroutinefunction(obj.content):
            return obj.content()

        return obj


class Component(object, metaclass=NewInitCaller):
    content: Optional[Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]]

    def __await__(self) -> Any:
        if hasattr(self, "content") and inspect.iscoroutinefunction(self.content):
            return self.content().__await__()
