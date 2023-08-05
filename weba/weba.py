import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from weba.utils import find_open_port

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>weba</title>
        </head>
        <body>
            <h1>weba</h1>
        </body>
    </html>
    """


def _uvicorn_server() -> uvicorn.Server:
    config = uvicorn.Config(app, port=find_open_port(), log_level="error")
    return uvicorn.Server(config=config)


def run() -> None:
    server = _uvicorn_server()
    server.run()


async def async_run() -> None:
    server = _uvicorn_server()
    await server.serve()
