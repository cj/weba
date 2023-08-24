from functools import wraps
from typing import Any, ParamSpec, TypeVar

from dominate.dom_tag import Callable
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse

from weba.document import get_document
from weba.middleware import WebaMiddleware
from weba.utils import weba_encoder_decorator

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

    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
    )

    return app


app = load_app()
doc = get_document()


@app.get("/")
async def index():
    return doc.render()
