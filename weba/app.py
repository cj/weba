from typing import Any, ParamSpec, TypeVar

from dominate.dom_tag import Callable
from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
)
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette_cramjam.middleware import CompressionMiddleware

from .document import get_document
from .env import env
from .middleware import WebaMiddleware
from .utils import load_status_code_page, weba_encoder_decorator

P = ParamSpec("P")
R = TypeVar("R")


class WebaFastAPI(FastAPI):
    def __init__(self, *args, **kwargs):  # type: ignore
        super().__init__(*args, **kwargs)

        for method in ["get", "post", "put", "delete", "patch", "options"]:
            self.add_custom_method(method)

    def add_custom_method(self, method_name: str):
        fastapi_method = getattr(FastAPI, method_name)

        def decorator(*args, **kwargs):  # type: ignore
            def wrapper(func: Callable):  # type: ignore
                return fastapi_method(self, *args, **kwargs)(weba_encoder_decorator(func))  # type: ignore

            return wrapper  # type: ignore

        setattr(self, method_name, decorator)

    def form(self, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            return FastAPI.get(self, f"/{func.__name__}", **kwargs)(weba_encoder_decorator(func))

        return decorator


def load_app() -> WebaFastAPI:
    app = WebaFastAPI(default_response_class=HTMLResponse)

    app.add_middleware(
        WebaMiddleware,
    )

    app.add_middleware(CompressionMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        status_code = exc.status_code

        html = await load_status_code_page(status_code, request)

        if html:
            # we return 200 if live reload is enabled, otherwise the page will not reload
            return HTMLResponse(html, status_code=200 if env.live_reload else status_code)

        return await http_exception_handler(request, exc)

    return app


app = load_app()
doc = get_document()


@app.get("/")
async def index():
    # raise Exception("test")
    return doc.render()
