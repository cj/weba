from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tag import Tag

current_parent: ContextVar[Tag | None] = ContextVar("current_parent", default=None)
