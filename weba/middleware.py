from typing import List, Optional, Pattern

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .build import build
from .document import WebaDocument, get_document
from .env import env


def weba_document(request: Request) -> WebaDocument:
    return request.scope["weba_document"]


class WebaMiddleware:
    app: ASGIApp
    exclude_paths: List[str]
    include_paths: List[str]
    scope: Scope
    receive: Receive
    send: Send

    def __init__(
        self,
        app: ASGIApp,
        exlcude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
    ) -> None:
        self.app = app
        self.exclude_paths = env.exclude_paths.extend(exlcude_paths or []) or []
        self.include_paths = env.include_paths.extend(include_paths or []) or []

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        self.scope = scope
        self.receive = receive
        self.send = send

        if scope["type"] != "http":
            return await self.app(scope, receive, self.handle_lifespan)

        # if exclude_paths is not empty we use not any() to check if the path is in the exclude_paths
        # and skip it, otherwise we check if the path is in the include_paths and skip it if it is not
        if not any(
            scope["path"].startswith(exclude_path)
            or isinstance(exclude_path, Pattern)
            and exclude_path.match(scope["path"])
            for exclude_path in self.exclude_paths
        ) and not any(
            scope["path"].startswith(include_path)
            or isinstance(include_path, Pattern)
            and include_path.match(scope["path"])
            for include_path in self.include_paths
        ):
            scope["weba_document"] = get_document()

        await self.app(scope, receive, send)

    async def handle_lifespan(self, message: Message):
        if message["type"] == "lifespan.startup.complete":
            await build.run()

        await self.send(message)
