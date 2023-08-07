import asyncio
import os

import aiofiles
from aiofiles import os as aiofiles_io
from icecream import inspect

from .env import env


class Build:
    has_project_tailwind_config: bool

    def __init__(self):
        project_tailwind_config = os.path.join(
            env.project_root_path,
            "tailwind.config.js",
        )

        self.has_project_tailwind_config = os.path.exists(project_tailwind_config)

    async def run(self):
        """
        Run the build process.
        """

        await self.create_weba_hidden_directory()
        await self.create_tailwind_config()
        await self.create_tailwind_css_file()
        await self.run_tailwindcss()

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

        if not self.has_project_tailwind_config:
            async with aiofiles.open(
                os.path.join(
                    env.weba_path,
                    "tailwind.config.js",
                ),
                "w",
            ) as f:
                await f.write(self.tailwind_config())

    def tailwind_config(self):
        ignored_folders = "|".join(env.ignored_folders)

        return inspect.cleandoc(
            f"""
            /** @type {{import('tailwindcss').Config}} */
            const defaultTheme = require('tailwindcss/defaultTheme')

            module.exports = {{
              content: [
                '../!({ignored_folders})/**/*.py',
                '../!({ignored_folders})/**/*._hs',
              ],
              theme: {{
                extend: {{
                  fontFamily: {{
                    sans: ['Inter var', ...defaultTheme.fontFamily.sans],
                  }},
                }},
              }},
              plugins: [
                require('@tailwindcss/typography'),
                // require('@tailwindcss/forms'),
                require('@tailwindcss/aspect-ratio'),
                require('@tailwindcss/container-queries'),
              ],
            }}
            """
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
            cwd=env.project_root_path if self.has_project_tailwind_config else env.weba_path,
        )

        await process.wait()


build = Build()
