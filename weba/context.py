from contextvars import ContextVar

from .tag import Tag

current_parent: ContextVar[Tag | None] = ContextVar("current_parent", default=None)
