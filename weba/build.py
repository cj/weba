import asyncio
import hashlib
import inspect
import os
import re
import shutil
from time import time
from typing import Annotated, Any, Dict, List, Optional, Text

import aiofiles
import aiohttp
from aiofiles import os as aiofiles_io
from jsmin import jsmin  # type: ignore

from .env import env

# from .packages import download_packages
from .utils import generate_keys, minimize_behavior  # type: ignore


def get_file_hash(file_path: Text) -> Text:
    """
    Get the hash of a file.

    If live reload is enabled, the hash will be the current time.
    """

    if env.live_reload:
        return str(time()).replace(".", "")

    # NOTE: This is only used to stop the browser from caching the file
    hash_md5 = hashlib.md5()  # noqa: S324

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def get_string_hash(string: Text) -> Text:
    if env.live_reload:
        return str(time()).replace(".", "")

    """
    Get the hash of a string.
    """
    hash_md5 = hashlib.md5()  # noqa: S324
    hash_md5.update(string.encode())

    return hash_md5.hexdigest()


def extract_name_version(url: str) -> str:
    if url.startswith("https://cdn.tailwindcss.com"):
        tw_pattern = r"(?P<start>.*\/)(?P<version>\d+(\.\d+){2})(\?plugins=)(?P<end>.*)"

        if not (tw_match := re.match(tw_pattern, url)):
            return url.split("/")[-1]

        plugins = "-".join(tw_match["end"].split(","))

        return f"1-tw-{plugins}-{tw_match['version']}"

    pattern = r".*\/(?P<name>.+)@(?P<version>\d+(\.\d+){0,3})\/.*\.(?P<ext>\w+)"

    if not (match := re.match(pattern, url)):
        return url.split("/")[-1]

    if match["name"] == "htmx.org":
        htmx_pattern = r".*\/(?:.+)@(?P<version>\d+(\.\d+){0,3})\/.+\/(?P<name>[\w-]*)\.(?P<ext>\w+)"

        if not (htmx_match := re.match(htmx_pattern, url)):
            return url.split("/")[-1]

        name = htmx_match["name"]
        version = "1" if name == "htmx" else "2"

        return f"{version}-{name}-{htmx_match['version']}.{htmx_match['ext']}"

    filename = f"{match['name']}-{match['version']}.{match['ext']}"

    if filename.startswith("daisyui-"):
        filename = f"2-{filename}"

    return filename


class Build:
    _has_project_tailwind_config: bool
    """ Static directory hash is used to bust the cache. """
    _project_tailwind_config = os.path.join(
        env.project_root_path,
        "tailwind.config.js",
    )
    _files: Optional[Dict[Annotated[str, "file name"], str]]
    _tw_css_files: Optional[Text]
    _css_files: Optional[Text]
    _js_files: Optional[Text]
    _hs_files: Optional[Text]

    def __init__(self):
        self._has_project_tailwind_config = os.path.exists(self._project_tailwind_config)
        self._files = None
        self._cache_dir = os.path.join(env.weba_path, "cache")

    @property
    def files(self) -> Dict[Annotated[str, "file name"], str]:
        """
        Get the file hashes.
        """

        if not self._files:
            self._files = {
                file_name: ""
                if re.match(r".*(-[\d\.]{2,})\.\w+$", file_name)
                else get_file_hash(f"{env.weba_public_dir}/{file_name}")
                for file_name in os.listdir(env.weba_public_dir)
            }

        return self._files

    @property
    def tailwind_config(self):
        ignored_folders = "|".join(env.ignored_folders)

        return inspect.cleandoc(
            f"""
            module.exports = {{
              darkMode: ['class', '[data-theme="dark"]'],
              safelist: [
                  'min-h-screen',
                  'overflow-auto',
              ],
              content: [
                '../**/*.{{py,_hs}}',
                '../**/{{pages,components,layouts}}/*.{{py,_hs}}',
                '{{pages,components,layouts}}/*.{{py,_hs}}',
                '../!({ignored_folders})/**/*.{{py,_hs}}',
                '!(__pycache__).{{py,_hs}}',
              ],
              plugins: [
                {", ".join([f"require('@tailwindcss/{plugin}')" for plugin in env.tw_plugins])}
              ],
            }}
            """
        )

    async def run(self):
        """
        Run the build process.
        """

        await self.create_weba_hidden_directory()
        await self.create_tailwind_config()
        await self.create_secrets()
        # NOTE: Some day :)
        # await download_packages()

        files: Any = []

        if env.live_reload:
            # plugins = ",".join(env.tw_plugins)

            files += [
                self.create_files([f"https://unpkg.com/htmx.org@{env.htmx_version}/dist/htmx.js"]),
                self.create_tailwind_css_file(),
                # self.create_files([f"https://cdn.tailwindcss.com/{env.tw_version}?plugins={plugins}"]),
                # self.create_files(env.tw_css_files),
                self.create_files(env.css_files),
                self.create_files(env.js_files),
                self.create_files(env.hs_files),
                self.create_htmx_extension_files(),
            ]
        else:
            files += [
                self.create_tailwind_css_file(),
                self.create_scripts_files(),
                self.create_hyperscript_files(),
            ]

        await asyncio.gather(*files)

        # if not env.live_reload:
        await self.run_tailwindcss()

    async def create_files(self, files: List[Text], return_as_text: bool = False) -> str:
        """
        Create the files.
        """

        if not files:
            return ""

        file_content = ""

        for file in files:
            if file.startswith("http"):
                # Download the file, check if it has <name>@x.x.x (version number), and use that for the filename
                file_path = os.path.join(self._cache_dir, extract_name_version(file))

                if not return_as_text and os.path.exists(file_path):
                    # copy the file from the cache to the static directory, overwriting the old file
                    shutil.copy(file_path, env.weba_public_dir)
                    continue

                async with aiohttp.ClientSession() as session:
                    async with session.get(file) as resp:
                        if resp.status != 200:
                            raise Exception(f"Could not download file {file}")  # sourcery skip: raise-specific-error

                        content = await resp.text()
                        # https://cdn.jsdelivr.net/npm/<name>@<version>/dist/full.css
                        # match the name and version from the url, to make the filename <name>-<version>.css
                        async with aiofiles.open(file_path, "w") as f:
                            await f.write(content)

                            if return_as_text:
                                file_content += f"{content}{'' if file.endswith('._hs') else ';'}"
                            else:
                                shutil.copy(file_path, env.weba_public_dir)
            else:
                file_name = file.split("/")[-1]
                public_file_path = os.path.join(env.weba_public_dir, file_name)

                async with aiofiles.open(public_file_path, "w") as f:
                    async with aiofiles.open(file, "r") as f2:
                        content = await f2.read()
                        if return_as_text:
                            file_content += f"{content}{'' if file.endswith('._hs') else ';'}"
                        else:
                            await f.write(content)

                if return_as_text:
                    os.remove(public_file_path)

        return file_content

    async def create_secrets(self):
        if env.is_prod:
            return

        secrets_path = os.path.join(env.weba_path, ".secrets")

        # remove file if exists
        if os.path.exists(secrets_path):
            return

        env.cookie_secrets = generate_keys(3)
        session_secret_key: str = generate_keys(1)[0]
        env.session_secret_key = session_secret_key
        cookie_secrets = ",".join(env.cookie_secrets)

        # make the .secrets file
        async with aiofiles.open(secrets_path, "w") as f:
            await f.write(
                inspect.cleandoc(
                    f"""
                    WEBA_COOKIE_SECRETS={cookie_secrets}
                    WEBA_SESSION_SECRET_KEY={session_secret_key}
                    """
                )
            )

    async def create_htmx_extension_files(self, return_as_text: bool = False):
        return await self.create_files(
            # TODO: Add @{env.htmx_version} and fix getting the filename and version
            [f"https://unpkg.com/htmx.org@{env.htmx_version}/dist/ext/{file}.js" for file in env.htmx_extentions],
            return_as_text=return_as_text,
        )

    async def create_scripts_files(self):
        """
        Create the scripts.js file.
        """

        scripts_js_path = os.path.join(env.weba_public_dir, "scripts.js")

        async with aiofiles.open(scripts_js_path, "w") as f:
            js = await self.create_files(
                [f"https://unpkg.com/htmx.org@{env.htmx_version}/dist/htmx.js"], return_as_text=True
            )

            js += ";".join(
                await asyncio.gather(
                    self.create_htmx_extension_files(return_as_text=True),
                    self.create_files(env.js_files, return_as_text=True),
                )
            )

            await f.write(jsmin(inspect.cleandoc(js)))

    async def create_hyperscript_files(self):
        """
        Create the hyperscript._hs file.
        """

        hyperscript_js_path = os.path.join(env.weba_public_dir, "hyperscript._hs")

        async with aiofiles.open(hyperscript_js_path, "w") as f:
            modules_contents = await self.create_files(env.hs_files, return_as_text=True)

            await f.write(minimize_behavior(modules_contents))

    async def create_tailwind_css_file(self):
        """
        Create the tailwind.css file.
        """

        tailwind_css_path = os.path.join(env.weba_path, "tailwind.css")

        async with aiofiles.open(tailwind_css_path, "w") as f:
            css = """
            @tailwind base;
            @tailwind components;
            @tailwind utilities;
            """

            tw_css = await self.create_files(env.tw_css_files, return_as_text=True)

            css += f"""
            @layer components {{
                {tw_css}
            }}
            """

            if not env.live_reload:
                additional_css = await self.create_files(env.css_files, return_as_text=True)

                css += f"{additional_css}"

                # This is so tailwindcss can find the classes
                for folder in ["pages", "components"]:
                    folder_path = os.path.join(os.path.dirname(__file__), folder)
                    if os.path.exists(folder_path):
                        weba_folder_path = os.path.join(env.weba_path, folder)
                        # remove the folder if it exists
                        if os.path.exists(weba_folder_path):
                            shutil.rmtree(weba_folder_path)
                        # copy the folder, but not __pycache__ folders
                        shutil.copytree(folder_path, weba_folder_path, ignore=shutil.ignore_patterns("__pycache__"))

            await f.write(inspect.cleandoc(css))

    async def run_tailwindcss(self):
        """
        Run tailwindcss.
        """

        cmds: List[str] = []

        if not env.live_reload:
            cmds += ["--minify"]

        process = await asyncio.create_subprocess_shell(
            f"{env.tw_cmd} {' '.join(cmds)} -i {env.weba_path}/tailwind.css -o {env.weba_public_dir}/styles.css",
            cwd=env.project_root_path if self._has_project_tailwind_config else env.weba_path,
        )

        await process.wait()

    async def create_weba_hidden_directory(self):
        """
        Create the hidden directory for weba.
        """

        if os.path.exists(env.weba_public_dir):
            shutil.rmtree(env.weba_public_dir)

        paths = [
            env.weba_path,
            env.weba_public_dir,
            self._cache_dir,
        ]

        for path in paths:
            if not os.path.exists(path):
                await aiofiles_io.mkdir(path)

    async def create_tailwind_config(self):
        """
        Create the tailwind config file.
        """

        if not self._has_project_tailwind_config:
            async with aiofiles.open(
                os.path.join(
                    env.weba_path,
                    "tailwind.config.js",
                ),
                "w",
            ) as f:
                await f.write(self.tailwind_config)


build = Build()
