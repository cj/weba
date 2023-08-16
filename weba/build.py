import asyncio
import hashlib
import os
import re
import shutil
from time import time
from typing import Annotated, Dict, List, Optional, Text

import aiofiles
import aiohttp
from aiofiles import os as aiofiles_io
from icecream import inspect

from .env import env


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
    pattern = r".*\/(?P<name>.+)@(?P<version>\d+(\.\d+){0,3})\/.*\.(?P<ext>\w+)"

    if not (match := re.match(pattern, url)):
        return url.split("/")[-1]

    if match["name"] == "htmx.org":
        htmx_pattern = r".*\/(?:.+)@(?P<version>\d+(\.\d+){0,3})\/.+\/(?P<name>[\w-]*)\.(?P<ext>\w+)"
        if htmx_match := re.match(htmx_pattern, url):
            return f"{htmx_match['name']}-{htmx_match['version']}.{htmx_match['ext']}"
        else:
            return url.split("/")[-1]

    return f"{match['name']}-{match['version']}.{match['ext']}"


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
                else get_file_hash(f"{env.static_dir}/{file_name}")
                for file_name in os.listdir(env.static_dir)
            }

        return self._files

    @property
    def tailwind_config(self):
        ignored_folders = "|".join(env.ignored_folders)

        return inspect.cleandoc(
            f"""
            module.exports = {{
              content: [
                '../**/*.{{py,_hs}}',
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
        await self.create_tailwind_css_file()
        await asyncio.gather(
            self.create_files(env.tw_css_files),
            self.create_files(env.css_files),
            self.create_files(env.js_files),
            self.create_hs_extension_files(),
            self.create_files([f"https://unpkg.com/htmx.org@{env.htmx_version}/dist/htmx.js"]),
        )
        await self.run_tailwindcss()

    async def create_files(self, files: List[Text]):
        """
        Create the files.
        """

        if not files:
            return

        for file in files:
            if file.startswith("http"):
                # Download the file, check if it has <name>@x.x.x (version number), and use that for the filename
                file_path = os.path.join(self._cache_dir, extract_name_version(file))

                if os.path.exists(file_path):
                    # copy the file from the cache to the static directory, overwriting the old file
                    shutil.copy(file_path, env.static_dir)
                    continue

                async with aiohttp.ClientSession() as session:
                    async with session.get(file) as resp:
                        if resp.status != 200:
                            raise Exception(f"Could not download file {file}")

                        content = await resp.text()
                        # https://cdn.jsdelivr.net/npm/<name>@<version>/dist/full.css
                        # match the name and version from the url, to make the filename <name>-<version>.css
                        async with aiofiles.open(file_path, "w") as f:
                            await f.write(content)
                            shutil.copy(file_path, env.static_dir)
            else:
                file_name = file.split("/")[-1]
                async with aiofiles.open(os.path.join(env.static_dir, file_name), "w") as f:
                    async with aiofiles.open(file, "r") as f2:
                        await f.write(await f2.read())

    async def create_hs_extension_files(self):
        return await self.create_files(
            # TODO: Add @{env.htmx_version} and fix getting the filename and version
            [f"https://unpkg.com/htmx.org@{env.htmx_version}/dist/ext/{file}.js" for file in env.htmx_extentions],
        )

    async def create_tailwind_css_file(self):
        """
        Create the tailwind.css file.
        """

        tailwind_css_path = os.path.join(env.weba_path, "tailwind.css")

        if not os.path.exists(tailwind_css_path):
            async with aiofiles.open(tailwind_css_path, "w") as f:
                css = """
                @tailwind base;
                @tailwind components;
                @tailwind utilities;
                """
                await f.write(inspect.cleandoc(css))

    async def run_tailwindcss(self):
        """
        Run tailwindcss.
        """

        process = await asyncio.create_subprocess_shell(
            f"tailwindcss -i {env.weba_path}/tailwind.css -o {env.static_dir}/styles.css",
            cwd=env.project_root_path if self._has_project_tailwind_config else env.weba_path,
        )

        await process.wait()

    async def create_weba_hidden_directory(self):
        """
        Create the hidden directory for weba.
        """

        if os.path.exists(env.static_dir):
            shutil.rmtree(env.static_dir)

        paths = [
            env.weba_path,
            env.static_dir,
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
