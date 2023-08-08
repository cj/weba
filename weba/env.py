import os
from pathlib import Path
from typing import Any, List

from dominate.dom_tag import Callable
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


def env_file() -> tuple[str, ...]:
    match os.environ.get("WEBA_ENV", "dev"):
        case "production" | "prod" | "prd":
            return (".env", ".env.local", ".env.prd", ".env.prod", ".env.production")
        case "staging" | "stg":
            return (".env", ".env.local", ".env.stg", ".env.staging")
        case "testing" | "test" | "tst":
            return (".env", ".env.local", ".env.tst", ".env.test", ".env.testing")
        case _:
            return (".env", ".env.local", ".env.dev", ".env.development")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="weba_",
        env_file=env_file(),
        extra="ignore",
    )

    port: int = 3334
    host: str = "127.0.0.1"
    env: str = "dev"
    live_reload: bool = False
    modules: List[Any] = []
    add_module: Callable[..., Any] = modules.append
    project_root_path: Path = Path(__file__).parent.parent
    weba_path: str = os.path.join(project_root_path, ".weba")
    static_dir: str = os.path.join(weba_path, "static")
    static_url: str = "/weba/static"
    ignored_folders: List[str] = [
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        weba_path,
        ".pytest_cache",
    ]
    pages_dir: str = (
        os.path.join(project_root_path, "pages")
        if os.path.exists(os.path.join(project_root_path, "pages"))
        else os.path.join(project_root_path, "app/pages")
    )
    exclude_paths: List[str] = []
    include_paths: List[str] = []


env = Settings()
