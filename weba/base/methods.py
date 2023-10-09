from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Union

from fastapi import Request, Response
from starlette.background import BackgroundTasks

if TYPE_CHECKING:
    from .component import Component
    from .page import Page


WebaMethodsException = Exception


class Methods:
    _kwargs: dict[str, Any]
    _args: tuple[Any, ...]

    @cached_property
    def _parent(self) -> Union["Page", "Component", None]:
        from .component import Component
        from .page import Page

        return next((arg for arg in self._args if isinstance(arg, (Page | Component))), None)

    @property
    def request(self) -> Request:
        request = self._kwargs.get("request") or (self._parent.request if self._parent else None)

        if not request:
            raise WebaMethodsException("No request found")

        return request

    @property
    def response(self) -> Response:
        response = self._kwargs.get("response") or (self._parent.response if self._parent else None)

        if not response:
            raise WebaMethodsException("No response found")

        return response

    @property
    def params(self) -> Dict[str, Any]:
        return self._kwargs.get("params") or (self._parent.params if self._parent else {})

    @property
    def background_tasks(self) -> BackgroundTasks:
        background_tasks = self._kwargs.get("background_tasks") or (
            self._parent.background_tasks if self._parent else None
        )

        if not background_tasks:
            raise WebaMethodsException("No background_tasks found")

        return background_tasks

    @property
    def session_store(self) -> Dict[str, Any]:
        return self._kwargs.get("session_store") or (
            self._parent.session_store if self._parent else self.request.session.setdefault("store", {})
        )
