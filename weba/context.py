from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .tag import Tag

# Context variable that tracks the current parent Tag during component rendering.
# This allows nested components to access their parent Tag context.
# Default is None when outside of a component render context.
current_parent: ContextVar[Tag | None] = ContextVar("current_parent", default=None)
