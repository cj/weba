from typing import Optional

import __main__
import uvicorn
from fastapi import FastAPI

from .app import app as weba_app
from .env import env
from .utils import find_open_port

uvicorn_running = False


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
    if not env.live_reload or hasattr(__main__, "__file__"):
        open_port = port or find_open_port()

        project_root_path = env.project_root_path.as_posix()

        return uvicorn.run(  # type: ignore
            app or "weba.app:app",
            port=open_port,
            log_level=log_level,
            reload=env.live_reload,
            reload_dirs=[project_root_path],
            reload_excludes=env.ignored_folders,
        )
