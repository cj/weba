import os
from typing import List, Optional, Pattern

from starlette.requests import Request
from starlette.staticfiles import StaticFiles
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
    staticfiles: StaticFiles
    scope: Scope
    receive: Receive
    send: Send

    def __init__(
        self,
        app: ASGIApp,
        exlcude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
    ) -> None:
        staticfiles_class = NoCacheStaticFiles if env.live_reload else StaticFiles

        self.app = app
        self.exclude_paths = env.exclude_paths.extend(exlcude_paths or []) or []
        self.include_paths = env.include_paths.extend(include_paths or []) or []
        self.staticfiles = staticfiles_class(directory=env.static_dir, check_dir=False)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        self.scope = scope
        self.receive = receive
        self.send = send

        if scope["type"] != "http":
            return await self.app(scope, receive, self.handle_lifespan)

        if scope["path"].startswith(env.static_url):
            scope["path"] = self.get_static_file_path(scope["path"])

            return await self.staticfiles(scope, receive, send)

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
        match message["type"]:
            case "lifespan.startup.complete":
                if env.live_reload or not os.path.exists(env.weba_path):
                    await build.run()
            case _:
                pass

        await self.send(message)

    def get_static_file_path(self, path: str) -> str:
        # Remove the "/static" prefix before forwarding the request
        path = path.replace(env.static_url, "")
        # Remove the -<hash> part from <filename>-<hash>.<ext> so it becomes <filename>.<ext>
        splits = path.rsplit("-")

        if len(splits) > 1:
            path = f"{splits[0]}.{splits[1].split('.')[-1]}"

        return path


class NoCacheStaticFiles(StaticFiles):
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async def no_cache_send(message: Message):
            if message.get("type") == "http.response.start":
                headers = message.get("headers", [])
                headers.append((b"cache-control", b"no-store"))
                message["headers"] = headers
            await send(message)

        await super().__call__(scope, receive, no_cache_send)
