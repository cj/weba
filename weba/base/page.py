import inspect
from typing import Any, AsyncContextManager, Callable, ContextManager, Coroutine, Optional

from ..document import WebaDocument
from ..env import env
from ..utils import is_asynccontextmanager
from .methods import Methods

WebaPageException = Exception


LayoutType = type(ContextManager) | type(AsyncContextManager)


class Page(Methods):
    title: str = "Weba"

    before_render: Optional[Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]]
    content: Optional[Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]]

    title: str = "Weba"

    layout: Optional[LayoutType]

    # TODO: Remove this init and move to methods
    def __init__(
        self,
        *args: Any,
        title: Optional[str] = None,
        document: Optional[WebaDocument] = None,
        **kwargs: Any,
    ) -> None:
        title = title or self.title
        self._document = document or WebaDocument(title=title)
        self._document.title = title

        self._args = args
        self._kwargs = kwargs

    async def render(self) -> str:
        await self._before_render()

        with self._document as doc:
            await self._render_content

        return doc.render(pretty=env.pretty_html)

    async def _before_render(self):
        # check to see if before render is defined if so call it
        if hasattr(self, "before_render"):
            if inspect.iscoroutinefunction(self.before_render):
                await self.before_render()
            elif callable(self.before_render):
                self.before_render()

    @property
    def document(self) -> WebaDocument:
        return self._document

    @property
    def doc(self) -> WebaDocument:
        return self._document

    @property
    async def _content(self) -> Optional[Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]]:
        if not hasattr(self, "content"):
            raise WebaPageException("content is not set")

        if inspect.iscoroutinefunction(self.content):
            await self.content()
        elif callable(self.content):
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
