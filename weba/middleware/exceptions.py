from fastapi import Request
from fastapi.exception_handlers import (
    http_exception_handler,
)
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# from shellous import sh
from ..env import env
from ..utils import load_status_code_page


async def weba_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    if not request.headers.get("accept", "").startswith("text/html"):
        return await http_exception_handler(request, exc)

    status_code = exc.status_code

    html = await load_status_code_page(status_code, request)

    if html:
        # we return 200 if live reload is enabled, otherwise the page will not reload
        return HTMLResponse(html, status_code=200 if env.live_reload else status_code)


async def weba_unhandled_exception_handler(
    request: Request,
    _exc: Exception,
):
    status_code = 500

    html = await load_status_code_page(status_code, request)

    if html:
        # we return 200 if live reload is enabled, otherwise the page will not reload
        return HTMLResponse(html, status_code=200 if env.live_reload else status_code)
