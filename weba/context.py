from __future__ import annotations

from contextvars import ContextVar
from functools import cached_property
from typing import Any, ClassVar


class ContextMixin:
    weba_context: ClassVar[ContextVar[Any]] = ContextVar("current_weba_context")
    _weba_context_token: Any

    @cached_property
    def context(self):
        context = self.weba_context.get(None)

        if not context:
            self._weba_context_token = self.weba_context.set(self)
            context = self

        return context

    def __enter__(self):
        return self.context

    async def __aenter__(self):
        return self.__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        pass

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.__exit__(exc_type, exc_val, exc_tb)


class Context(ContextMixin):
    def __enter__(self):
        self._weba_context_token = self.weba_context.set(self)

        return self.context

    async def __aenter__(self):
        return self.__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.weba_context.reset(self._weba_context_token)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.__exit__(exc_type, exc_val, exc_tb)
