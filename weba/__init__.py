from fastapi import Depends

from . import tags
from .app import app
from .document import WebaDocument
from .env import env
from .middleware import weba_document
from .ui import html_tag, ui
from .weba import async_run, run, uvicorn_server

document = weba_document
Document = WebaDocument

__all__ = [
    "app",
    "uvicorn_server",
    "run",
    "async_run",
    "env",
    "WebaDocument",
    "Document",
    "weba_document",
    "document",
    "ui",
    "html_tag",
    "tags",
    "Depends",
]
