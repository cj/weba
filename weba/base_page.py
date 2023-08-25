import inspect
from typing import Any, Callable, Coroutine, Dict, Optional

from fastapi import Request, Response

from .document import WebaDocument

WebaPageException = Exception


class BasePage:
    content: Optional[Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]]

    def __init__(
        self,
        title: str = "Weba",
        document: Optional[WebaDocument] = None,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._document = document or WebaDocument(title=title)
        self._request = request
        self._response = response
        self._params = params or {}

    async def render(self) -> str:
        content = self.content

        if not content:
            raise WebaPageException("content is not set")

        with self.doc.body:
            if inspect.iscoroutinefunction(content):
                await content()
            else:
                content()

        return self.doc.render()

    @property
    def document(self) -> WebaDocument:
        return self._document

    @property
    def doc(self) -> WebaDocument:
        return self.document

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
