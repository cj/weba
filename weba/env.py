import logging
import os
import traceback as tb
from pathlib import Path
from typing import Any, List, Tuple, Type

from dominate.dom_tag import Callable
from dotenv import load_dotenv
from pydantic import AliasChoices, Field, model_validator  # type: ignore
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict

load_dotenv()

uvicorn_logger = logging.getLogger("uvicorn")


def env_file() -> tuple[str, ...]:
    match os.getenv("WEBA_ENV", "dev"):
        case "production" | "prod" | "prd":
            return (".env", ".env.local", ".env.prd", ".env.prod", ".env.production")
        case "staging" | "stg":
            return (".env", ".env.local", ".env.stg", ".env.staging")
        case "testing" | "test" | "tst":
            return (".env", ".env.local", ".env.tst", ".env.test", ".env.testing")
        case _:
            return (".env", ".env.local", ".env.dev", ".env.development")


class WebaCustomSource(EnvSettingsSource):
    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,  # noqa: ARG002
        value: Any,
        value_is_complex: bool,  # noqa: ARG002
    ) -> Any:
        if not value:
            return value

        if isinstance(value, str) and field_name in {
            "css_files",
            "js_files",
            "tw_plugins",
            "tw_css_files",
            "ignored_folders",
            "exclude_paths",
            "include_paths",
            "modules",
        }:
            return [str(v).strip() for v in value.split(",")]

        return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="weba_",
        env_file=env_file(),
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            WebaCustomSource(settings_cls),
        )

    handle_exception: Callable[..., Any] = lambda _e: [  # noqa: E731
        uvicorn_logger.error(line) for line in tb.format_exc().splitlines()
    ]
    port: int = Field(
        3334,
        validation_alias=AliasChoices("weba_port", "port"),
    )
    host: str = Field(
        "127.0.0.1",
        validation_alias=AliasChoices("weba_host", "host"),
    )
    env: str = "dev"
    live_reload: bool = False
    live_reload_url: str = "/weba/live-reload"
    modules: List[Any] = []
    project_root_path: Path = Path(__file__).parent.parent
    weba_path: str = os.path.join(project_root_path, ".weba")
    static_dir: str = os.path.join(project_root_path, ".weba", "static")
    static_url: str = "/weba/static"
    tw_version: str = "3.3.3"
    tw_plugins: List[str] = ["typography", "aspect-ratio"]
    tw_css_files: List[str] = ["https://cdn.jsdelivr.net/npm/daisyui@3.6.2/dist/full.css"]
    """
    These css files will be included in the tailwind build process.
    Wrapped in @layer components {}, so that tailwind will purge unused css classes.
    In live_reload mode, these files in their own file, this results in larger files but quicker compile times.
    """
    css_files: List[str] = []
    js_files: List[str] = []
    htmx_version: str = "1.9.5"
    htmx_extentions: List[str] = ["head-support", "json-enc"]
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
    forms_dir: str = (
        os.path.join(project_root_path, "forms")
        if os.path.exists(os.path.join(project_root_path, "forms"))
        else os.path.join(project_root_path, "app/forms")
    )
    exclude_paths: List[str] = []
    include_paths: List[str] = []

    @model_validator(mode="after")
    @classmethod
    def _(cls, settings: Any):
        if settings.live_reload:
            settings.add_htmx_extention("ws")

        return settings

    def add_htmx_extention(self, *extentions: str):
        self.htmx_extentions.extend(extentions)

    def add_css_file(self, *files: str):
        self.css_files.extend(files)

    def add_js_file(self, *files: str):
        self.js_files.extend(files)

    def add_tw_plugin(self, *plugins: str):
        self.tw_plugins.extend(plugins)

    def add_tw_css_file(self, *files: str):
        self.tw_css_files.extend(files)

    def add_ignored_folder(self, *folders: str):
        self.ignored_folders.extend(folders)

    def add_exclude_path(self, *paths: str):
        self.exclude_paths.extend(paths)

    def add_include_path(self, *paths: str):
        self.include_paths.extend(paths)

    def add_module(self, *modules: Any):
        self.modules.extend(modules)

    @property
    def is_test(self) -> bool:
        return self.env in ("test", "testing", "tst")

    @property
    def is_dev(self) -> bool:
        return self.env in ("dev", "development", "dev")

    @property
    def is_stg(self) -> bool:
        return self.env in ("staging", "stg")

    @property
    def is_prod(self) -> bool:
        return self.env in ("production", "prod", "prd")


env = Settings()  # type: ignore
