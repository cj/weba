import asyncio
import contextlib
import inspect
import os
import re
import socket
from functools import wraps
from importlib import util
from typing import Any, Coroutine, Dict, List, Optional, Tuple, TypeVar, cast

from cryptography.fernet import Fernet
from dominate.dom_tag import Callable
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder as _jsonable_encoder
from starlette.background import BackgroundTasks

from .document import WebaDocument, get_document
from .env import env

current_dir_path = os.path.dirname(os.path.abspath(__file__))


def find_open_port(port: int = env.port, max_port: int = 65535):
    while port <= max_port:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            location = (env.host, port)
            check = sock.connect_ex(location)

            if check != 0:
                env.port = port
                return port

            port += 1

    raise IOError("no free ports")


def weba_encoder(obj: Any, *args: Any, **kwargs: Any):
    # type_str = f"{type(obj)}"

    if isinstance(obj, List):
        return ("").join([weba_encoder(item, *args, **kwargs) for item in obj])  # type: ignore

    # if (
    #     "dominate" in type_str or "weba.document" in type_str or "ui." in type_str or isinstance(obj, Component)
    # ) and hasattr(obj, "render"):
    if hasattr(obj, "render"):
        return obj.render(pretty=env.pretty_html)

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


# Find page file based on url
def find_page(path: Any, pages_dir: Optional[str] = env.pages_dir) -> Tuple[str | None, Dict[str, str]]:
    pages_dir = pages_dir or env.pages_dir
    path = f"{path}"
    found_path = None
    params: Dict[str, str] = {}

    if path == "/":
        path = "/index"

    """Find page file based on url."""
    for root, dirs, files in os.walk(pages_dir, topdown=True):
        # ignore pyc files and __pycache__ directories
        files = [f for f in files if not f.endswith(".pyc")]
        dirs[:] = [d for d in dirs if not d.endswith("__pycache__")]
        # remove the pages_dir from the root
        root = root.replace(pages_dir, "")

        # if the path is the root, then we need to look for an index.py file
        # matches /pages/admin/orders/index.py
        if root == path:
            found_path = f"{pages_dir}/{root}/index.py"

        # Check if the path matches a file name in files
        # matches /pages/login.py
        if f"{path[1:]}.py" in files:
            found_path = f"{pages_dir}/{path[1:]}.py"

        # remove the last /whatever from path
        # matches /admin/orders/2342424
        # matches /pages/admin/orders/__id__.py
        end_path = "/".join(path.split("/")[:-1])

        if not bool(dirs) and end_path == root:
            file = [f for f in files if f.startswith("__") and f != "__init__.py"]
            file = file[0] if bool(file) else "index.py"
            last_path = path.split("/")[-1]
            # make the key from __whatever__.py to whatever
            key = file.split(".")[0].replace("__", "")
            found_path = f"{pages_dir}{end_path}"
            if os.path.isdir(f"{found_path}/{last_path}") or file.startswith("__"):
                params[key] = last_path
                found_path = f"{found_path}/{file}"
            else:
                params = {}
                found_path = f"{found_path}/{last_path}.py"

    if found_path and not os.path.isfile(found_path):
        found_path = None

    return found_path, params


def load_page_class(file_path: str) -> Any:
    spec = cast(Any, util.spec_from_file_location("page_module", file_path))
    page_module = util.module_from_spec(spec)
    spec.loader.exec_module(page_module)
    classes = [cls_name for cls_name, cls_obj in inspect.getmembers(page_module) if inspect.isclass(cls_obj)]
    page_class = [cls for cls in classes if cls.endswith("Page") and cls != "Page"].pop()
    return getattr(page_module, page_class)


def merge_class(class_str: str, kwargs: Dict[str, Any]) -> str:
    """Merges different class kwargs into one string."""
    if "cls" in kwargs or "class_" in kwargs or "class" in kwargs or "_class" in kwargs or "className" in kwargs:
        class_str += (
            " "
            + kwargs.pop("cls", "")
            + kwargs.pop("class", "")
            + kwargs.pop("class_", "")
            + kwargs.pop("_class", "")
            + kwargs.pop("className", "")
        )

    # make sure there is only one space
    class_str = re.sub(r"\s+", " ", class_str)
    return class_str.strip()


def merge_hs(hs_str: str, kwargs: Dict[str, Any]) -> str:
    """Merges different hs kwargs into one string."""
    if "data-hs" in kwargs or "_" in kwargs or "_hs" in kwargs or "hyperscript" in kwargs:
        hs_str += (
            " " + kwargs.pop("hs", "") + kwargs.pop("_", "") + kwargs.pop("_hs", "") + kwargs.pop("hyperscript", "")
        )

    return hs_str.strip()


async def load_page(
    path: int | str,
    request: Request,
    response: Optional[Response] = None,
    document: Optional[WebaDocument] = None,
    pages_dir: str | None = None,
    background_tasks: Optional[BackgroundTasks] = None,
) -> str | None:
    page_path, params = find_page(path, pages_dir=pages_dir)

    if not page_path:
        return None

    document = document or get_document()

    params = (params or {}) | request.query_params._dict  # type: ignore

    page = load_page_class(page_path)(
        document=get_document(request=request),
        request=request,
        response=response,
        params=params,
        background_tasks=background_tasks,
    )

    return await page.render()


async def load_status_code_page(
    status_code: int,
    request: Request,
    response: Optional[Response] = None,
) -> str | None:
    return await load_page(status_code, request, response) or await load_page(
        status_code,
        request,
        response,
        pages_dir=os.path.join(current_dir_path, "pages"),
    )


def generate_keys(n: int) -> List[str]:
    return [Fernet.generate_key().decode() for _ in range(n)]


def is_asynccontextmanager(func: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]):
    """Check if the given function/method is decorated with asynccontextmanager."""
    # Try to get the coroutine object without actually running the function
    coroutine = func()

    try:
        return isinstance(coroutine, contextlib.AbstractAsyncContextManager)
    finally:
        if hasattr(coroutine, "close"):
            coroutine.close()  # close the coroutine since we won't await it


def read_public_file(file_path: str) -> str:
    with open(f"{env.public_dir}/{file_path}", "r") as file:
        return file.read()


svg_pattern = r"<svg[^>]*>(.*?)<\/svg>"


def read_svg(file: Optional[str] = None, svg: Optional[str] = None) -> Tuple[str, str | None]:
    if file:
        svg = read_public_file(file)

    if not svg:
        raise ValueError("file or svg must be set")

    view_box_split = svg.split("viewBox=")

    view_box = view_box_split[1].split('"')[1] if len(view_box_split) > 1 else None

    svg = re.sub(svg_pattern, r"\1", svg, flags=re.DOTALL)

    return (svg, view_box)


def read_public_svg(file: str) -> Tuple[str, str | None]:
    return read_svg(svg=read_public_file(file))


def get_static_file_path(path: str) -> str:
    # Remove the "/static" prefix before forwarding the request
    path = path.replace(env.weba_public_url, "")

    return re.sub(r"\-[\d\w]{15,}(?=\.\w+$)", "", path)


def minimize_behavior(unminimized_behavior: str) -> str:
    lines = unminimized_behavior.split("\n")
    minimized_lines = [line.strip() for line in lines if line.strip()]
    return " ".join(minimized_lines)
