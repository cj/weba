from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from weba.middleware import WebaMiddleware


def load_app() -> FastAPI:
    app = FastAPI(default_response_class=HTMLResponse)

    app.add_middleware(
        WebaMiddleware,
    )

    return app


app = load_app()
