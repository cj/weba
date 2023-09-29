from typing import Any, Optional

import __main__
import nest_asyncio
import uvicorn
from fastapi import FastAPI

from .app import app as weba_app
from .app import doc
from .env import env
from .utils import find_open_port

uvicorn_running = False

nest_asyncio.apply()  # type: ignore


def uvicorn_server(
    port: Optional[int],
    host: Optional[str] = None,
    app: Optional[FastAPI] = None,
    log_level: str = "info",
) -> uvicorn.Server:
    open_port = port or find_open_port()
    host = host or env.host

    config = uvicorn.Config(
        app or weba_app,
        port=open_port,
        host=host,
        log_level=log_level,
        lifespan="on",
        loop="asyncio",
    )

    return uvicorn.Server(config=config)


def run(
    port: Optional[int] = None,
    app: Optional[FastAPI] = None,
    host: Optional[str] = None,
    log_level: str = "info",
) -> None:
    if doc.body:

        @weba_app.get("/")
        async def index_page():
            # csrf_token = request.cookies.get("csrftoken", None)
            # doc.body["hx-headers"] = raw(json.dumps({"x-csrftoken": f"{csrf_token}"}))
            return doc

    if not env.live_reload or hasattr(__main__, "__file__"):
        open_port = port or find_open_port()
        host = host or env.host

        project_root_path = env.project_root_path.as_posix()

        uvicorn_args: Any = {
            "app": app or "weba.app:app",
            "port": open_port,
            "host": host,
            "log_level": log_level,
            "lifespan": "on",
            "loop": "asyncio",
        }

        if env.live_reload:
            uvicorn_args |= {
                "reload": True,
                "reload_dirs": [project_root_path],
                "reload_excludes": env.ignored_folders,
            }

        return uvicorn.run(  # type: ignore
            **uvicorn_args,
        )
