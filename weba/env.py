import logging
import os
import traceback as tb
from pathlib import Path
from typing import Any, List, Tuple, Type

from dominate.dom_tag import Callable
from dotenv import load_dotenv
from pydantic import AliasChoices, Field, model_validator  # type: ignore
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

load_dotenv()

uvicorn_logger = logging.getLogger("uvicorn")


def env_file() -> tuple[str, ...]:
    envs = ()
    env = os.getenv("WEBA_ENV", "dev")

    match env:
        case "production" | "prod" | "prd":
            envs = (".env", ".env.local", ".env.prd", ".env.prod", ".env.production")
        case "staging" | "stg":
            envs = (".env", ".env.local", ".env.stg", ".env.staging")
        case "testing" | "test" | "tst":
            envs = (".env", ".env.local", ".env.tst", ".env.test", ".env.testing")
        case _:
            envs = (".env", ".env.local", ".env.dev", ".env.development")

    if env not in ("production", "prod", "prd"):
        envs = (".weba/.secrets",) + envs

    return envs


class WebaCustomSource(DotEnvSettingsSource):
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
            "cookie_secrets",
            "cookie_include_list",
        }:
            return [str(v).strip() for v in value.split(",")]

        return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="weba_",
        env_file=env_file(),
        extra="ignore",
        env_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            WebaCustomSource(settings_cls),
            file_secret_settings,
        )

    handle_exception: Callable[..., Any] = lambda _e: [  # noqa: E731
        uvicorn_logger.error(line) for line in tb.format_exc().splitlines()
    ]
    cookie_secrets: List[Any] = []
    cookie_include_list: List[Any] = ["session", "csrftoken"]
    session_secret_key: str = ""
    port: int = Field(
        3334,
        validation_alias=AliasChoices("weba_port", "port"),
    )
    host: str = Field(
        "127.0.0.1",
        validation_alias=AliasChoices("weba_host", "host"),
    )
    env: str = "dev"
    pretty_html: bool = False
    live_reload: bool = False
    live_reload_url: str = "/weba/live-reload"
    cache_url: str = "memory://"
    modules: List[Any] = []
    project_root_path: Path = Path.cwd()
    weba_path: str = os.path.join(project_root_path, ".weba")
    weba_public_dir: str = os.path.join(project_root_path, ".weba", "public")
    weba_public_url: str = "/weba"
    # NOTE: Maybe use this down the line
    # packages_cdn: str = "https://cdn.jsdelivr.net/npm/"
    # packages: List[Any] = [
    #     {
    #         "name": "@tailwindcss/typography",
    #         "version": "0.5.10",
    #     },
    #     {
    #         "name": "@tailwindcss/aspect-ratio",
    #         "version": "0.4.2",
    #     },
    #     {
    #         "name": "daisyui",
    #         "version": "3.7.7",
    #     },
    # ]
    tw_cmd: str = "tailwindcss"
    tw_version: str = "3.3.3"
    tw_plugins: List[str] = ["typography", "aspect-ratio", "forms"]
    tw_css_files: List[str] = [
        # "https://cdn.jsdelivr.net/npm/daisyui@3.7.7/dist/full.css",
    ]
    """
    These css files will be included in the tailwind build process.
    Wrapped in @layer components {}, so that tailwind will purge unused css classes.
    In live_reload mode, these files in their own file, this results in larger files but quicker compile times.
    """
    css_files: List[str] = []
    js_files: List[str] = []
    hs_files: List[str] = []
    htmx_version: str = "1.9.6"
    htmx_extentions: List[str] = ["head-support", "json-enc"]
    htmx_boost: bool = True
    htmx_config: dict[str, Any] = {}
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
    public_dir: str = (
        os.path.join(project_root_path, "public")
        if os.path.exists(os.path.join(project_root_path, "public"))
        else os.path.join(project_root_path, "app/public")
    )
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

        if not os.getenv("WEBA_PRETTY_HTML"):
            settings.pretty_html = not settings.is_prod

        return settings

    def add_htmx_extention(self, *extentions: str):
        self.htmx_extentions.extend(extentions)

    def add_css_file(self, *files: str):
        self.css_files.extend(files)

    def add_js_file(self, *files: str):
        self.js_files.extend(files)

    def add_hs_file(self, *files: str):
        self.hs_files.extend(files)

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

    # def add_package(self, *packages: Any):
    #     self.packages.extend(packages)

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
