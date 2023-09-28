import asyncio
from typing import Any, ParamSpec, TypeVar

from dominate.dom_tag import Callable
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from securecookies import SecureCookiesMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

# from shellous import sh
from starlette.middleware.sessions import SessionMiddleware
from starlette_cramjam.middleware import CompressionMiddleware

from weba.middleware.exceptions import (
    weba_http_exception_handler,
    weba_unhandled_exception_handler,
)

from .build import build
from .document import get_document
from .env import env
from .middleware import CSRFMiddleware, WebaMiddleware
from .utils import weba_encoder_decorator

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
    if not env.cookie_secrets and not env.is_prod:
        asyncio.run(build.create_weba_hidden_directory())
        asyncio.run(build.create_secrets())

    app = WebaFastAPI(default_response_class=HTMLResponse)

    app.add_middleware(
        WebaMiddleware,
    )

    app.add_middleware(
        CompressionMiddleware,
    )

    app.add_middleware(
        CSRFMiddleware,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=env.session_secret_key,
        https_only=env.is_prod,
    )

    app.add_middleware(
        SecureCookiesMiddleware,
        secrets=env.cookie_secrets,
        cookie_httponly=True,
        cookie_secure=env.is_prod,
        included_cookies=env.cookie_include_list,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(  # type: ignore
        StarletteHTTPException,
        weba_http_exception_handler,
    )

    app.add_exception_handler(  # type: ignore
        Exception,
        weba_unhandled_exception_handler,
    )

    return app


app = load_app()
doc = get_document()
