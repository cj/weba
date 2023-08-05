from starlette.types import ASGIApp

from .settings import settings


class WebaMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        exlcude_paths: list[str],
        include_paths: list[str],
    ) -> None:
        self.app = app
        self.exlcude_paths = exlcude_paths
        self.include_paths = include_paths
