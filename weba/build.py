import asyncio
import os
from time import time
from typing import Optional, cast

import aiofiles
from aiofiles import os as aiofiles_io
from dirhash import dirhash  # type: ignore
from icecream import inspect

from .env import env


def create_static_dir_hash() -> str:
    """
    Get the static hash.
    """

    return cast(str, dirhash(env.static_dir, "sha1"))


class Build:
    _has_project_tailwind_config: bool
    _static_dir_hash: Optional[str]
    """ Static directory hash is used to bust the cache. """
    _project_tailwind_config = os.path.join(
        env.project_root_path,
        "tailwind.config.js",
    )

    def __init__(self):
        self._has_project_tailwind_config = os.path.exists(self._project_tailwind_config)
        self._static_dir_hash = None

    @property
    def static_dir_hash(self):
        """
        Return the static directory hash.
        """

        if not self._static_dir_hash:
            raise RuntimeError("Static directory hash is not set.")

        return self._static_dir_hash

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

        if not env.live_reload and not env.is_test():
            self._static_dir_hash = create_static_dir_hash()
        else:
            self._static_dir_hash = time().__str__()

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
