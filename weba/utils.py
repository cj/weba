import asyncio
import socket
from functools import wraps
from typing import Any, TypeVar

from dominate.dom_tag import Callable
from fastapi.encoders import jsonable_encoder as _jsonable_encoder

from .env import env


def find_open_port(port: int = env.port, max_port: int = 65535):
    while port <= max_port:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            location = (env.host, port)
            check = sock.connect_ex(location)

            if check != 0:
                return port

            port += 1

    raise IOError("no free ports")


def weba_encoder(obj: Any, *args: Any, **kwargs: Any):
    type_str = f"{type(obj)}"

    if ("dominate" in type_str or "weba.document" in type_str) and hasattr(obj, "render"):
        return obj.render()

    # Fall back to the original jsonable_encoder for other types
    return _jsonable_encoder(obj, *args, **kwargs)


T = TypeVar("T", bound=Callable[..., Any])


def weba_encoder_decorator(func: T) -> T:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any):
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return weba_encoder(result)

    return wrapper  # type: ignore
