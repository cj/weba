import asyncio
import hashlib
import os
from time import time
from typing import Annotated, Dict, Optional, Text

import aiofiles
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


class Build:
    _has_project_tailwind_config: bool
    """ Static directory hash is used to bust the cache. """
    _project_tailwind_config = os.path.join(
        env.project_root_path,
        "tailwind.config.js",
    )
    _file_hashes: Optional[Dict[Annotated[str, "file name"], str]]

    def __init__(self):
        self._has_project_tailwind_config = os.path.exists(self._project_tailwind_config)
        self._file_hashes = None

    @property
    def file_hashes(self) -> Dict[Annotated[str, "file name"], str]:
        """
        Get the file hashes.
        """

        if not self._file_hashes:
            self._file_hashes = {
                file_name: get_file_hash(f"{env.static_dir}/{file_name}") for file_name in os.listdir(env.static_dir)
            }

        return self._file_hashes

    @property
    def tailwind_config(self):
        ignored_folders = "|".join(env.ignored_folders)

        return inspect.cleandoc(
            f"""
            /** @type {{import('tailwindcss').Config}} */
            /** const defaultTheme = require('tailwindcss/defaultTheme') **/

            module.exports = {{
              content: [
                '../**/*.{{py,_hs}}',
                '../!({ignored_folders})/**/*.{{py,_hs}}',
              ],
              /**
              theme: {{
                extend: {{
                  fontFamily: {{
                    sans: ['Inter var', ...defaultTheme.fontFamily.sans],
                  }},
                }},
              }},
              **/
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
        await self.run_tailwindcss()

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

        if not os.path.exists(env.weba_path):
            await aiofiles_io.mkdir(env.weba_path)

        if not os.path.exists(env.static_dir):
            await aiofiles_io.mkdir(env.static_dir)

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
