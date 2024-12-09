from __future__ import annotations

from .component import Component, component_tag
from .context import current_parent
from .tag import Tag
from .ui import ui

tag = component_tag

__all__ = [
    "Component",
    "Tag",
    "component_tag",
    "current_parent",
    "tag",
    "ui",
]
