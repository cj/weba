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
    live_reload_url: str = "/weba/live-reload"
    modules: List[Any] = []
    add_module: Callable[..., Any] = modules.append
    project_root_path: Path = Path(__file__).parent.parent
    weba_path: str = os.path.join(project_root_path, ".weba")
    static_dir: str = os.path.join(weba_path, "static")
    static_url: str = "/weba/static"
    tw_plugins: List[str] = ["typography", "aspect-ratio", "container-queries"]
    tw_css_files: List[str] = ["https://cdn.jsdelivr.net/npm/daisyui@3.5.1/dist/full.css"]
    """
    These css files will be included in the tailwind build process.
    Wrapped in @layer components {}, so that tailwind will purge unused css classes.
    In live_reload mode, these files in their own file, this results in larger files but quicker compile times.
    """
    css_files: List[str] = []
    js_files: List[str] = []
    htmx_version: str = "1.9.4"
    htmx_extentions: List[str] = ["head-support", "ws-connect" if live_reload else ""]
    htmx_boost: bool = True
    ignored_folders: List[str] = [
        ".git",
        ".github",
        ".vscode",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".weba",
        "weba",
    ]
    pages_dir: str = (
        os.path.join(project_root_path, "pages")
        if os.path.exists(os.path.join(project_root_path, "pages"))
        else os.path.join(project_root_path, "app/pages")
    )
    exclude_paths: List[str] = []
    include_paths: List[str] = []

    def is_test(self) -> bool:
        return self.env in ("test", "testing", "tst")

    def is_dev(self) -> bool:
        return self.env in ("dev", "development", "dev")

    def is_stg(self) -> bool:
        return self.env in ("staging", "stg")

    def is_prod(self) -> bool:
        return self.env in ("production", "prod", "prd")


env = Settings()
