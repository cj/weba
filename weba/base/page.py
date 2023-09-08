import inspect
from typing import Any, AsyncContextManager, Callable, ContextManager, Coroutine, Dict, Optional

from fastapi import Request, Response

from ..document import WebaDocument
from ..env import env
from ..utils import is_asynccontextmanager

WebaPageException = Exception


LayoutType = type(ContextManager) | type(AsyncContextManager)


class Page:
    content: Optional[Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]]

    title: str = "Weba"

    layout: Optional[LayoutType] = None

    def __init__(
        self,
        title: Optional[str] = None,
        document: Optional[WebaDocument] = None,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        title = title or self.title
        self._document = document or WebaDocument(title=title)
        self.document.title = title

        self._request = request
        self._response = response
        self._params = params or {}
        self._session_store = self.request.session.setdefault("store", {})

    async def render(self) -> str:
        with self.doc.body:
            await self._render_content

        return self.doc.render(pretty=env.pretty_html)

    @property
    def document(self) -> WebaDocument:
        return self._document

    @property
    def doc(self) -> WebaDocument:
        return self.document

    @property
    def session_store(self) -> Dict[str, Any]:
        return self._session_store

    @property
    def request(self) -> Request:
        if not self._request:
            raise WebaPageException("request is not set")

        return self._request

    @property
    def response(self) -> Response:
        if not self._response:
            raise WebaPageException("response is not set")

        return self._response

    @property
    def params(self) -> Dict[str, Any]:
        return self._params

    @property
    async def _content(self) -> Optional[Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]]:
        if not self.content:
            raise WebaPageException("content is not set")

        if inspect.iscoroutinefunction(self.content):
            await self.content()
        else:
            self.content()

    @property
    async def _render_content(self) -> None:
        if hasattr(self, "layout") and self.layout:
            if is_asynccontextmanager(self.layout):
                async with self.layout():
                    await self._content
            else:
                with self.layout():
                    await self._content
        else:
            await self._content
