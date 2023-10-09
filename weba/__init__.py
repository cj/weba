from fastapi import Depends, Request, Response

from . import tags
from .app import app, doc
from .base import Component, Methods, Page, WebaPageException
from .cache import Cache, cache
from .document import WebaDocument, weba_document
from .env import Settings, env
from .ui import html_tag, ui
from .weba import run, uvicorn_server

document = weba_document
Document = WebaDocument

get = app.get
post = app.post
put = app.put
delete = app.delete
patch = app.patch
options = app.options
head = app.head
trace = app.trace

__all__ = [
    "app",
    "uvicorn_server",
    "run",
    "env",
    "WebaDocument",
    "Document",
    "weba_document",
    "document",
    "ui",
    "html_tag",
    "tags",
    "Depends",
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "options",
    "head",
    "trace",
    "doc",
    "Request",
    "Response",
    "Cache",
    "cache",
    "Page",
    "WebaPageException",
    "Component",
    "Settings",
    "Methods",
]
