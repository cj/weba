from typing import Optional

import uvicorn
from fastapi import FastAPI

from weba import app as weba_app
from weba.utils import find_open_port


def uvicorn_server(
    port: Optional[int],
    app: Optional[FastAPI] = None,
    log_level: str = "info",
) -> uvicorn.Server:
    open_port = port or find_open_port()

    config = uvicorn.Config(
        app or weba_app,
        port=open_port,
        log_level=log_level,
    )

    return uvicorn.Server(config=config)


def run(
    port: Optional[int] = None,
    app: Optional[FastAPI] = None,
    log_level: str = "info",
) -> None:
    server = uvicorn_server(
        port=port,
        app=app,
        log_level=log_level,
    )
    server.run()


async def async_run(
    port: Optional[int] = None,
    app: Optional[FastAPI] = None,
    log_level: str = "info",
) -> None:
    server = uvicorn_server(
        port=port,
        app=app,
        log_level=log_level,
    )
    await server.serve()
