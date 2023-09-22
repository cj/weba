import asyncio
import os
from typing import Any, List, cast

from aiohttp import ClientSession
from bs4 import BeautifulSoup, Tag

from .env import env

# Semaphore to limit concurrent downloads to 5
semaphore = asyncio.Semaphore(5)


async def fetch(url: str, session: ClientSession) -> str:
    async with session.get(url) as response:
        return await response.text()


async def download_file(url: str, path: str, session: ClientSession) -> None:
    # Acquire semaphore
    async with semaphore:
        async with session.get(url) as response:
            with open(path, "wb") as file:
                file.write(await response.read())


async def fetch_and_download(url: str, save_path: str = ".") -> None:
    async with ClientSession() as session:
        page_content = await fetch(url, session)

        if "html" not in page_content.lower():
            print(f"Non-HTML content found at {url}. Skipping.")
            return

        soup = BeautifulSoup(page_content, "html.parser")

        listings: Tag = cast(Tag, soup.find(class_="listing"))

        if not listings:
            print(f"No listings found at {url}. Skipping.")
            return

        rows = listings.find_all("tr")

        if not rows:
            print(f"No files found at {url}. Skipping.")
            return

        tasks: List[Any] = []

        for row in rows:
            name_cell: Tag = row.find("td", class_="name")
            if not name_cell:
                continue

            size_cell: Tag = row.find("td", class_="size")

            if not size_cell:
                continue

            name_cell.find("a")["href"]  # type: ignore

            name: str = name_cell.find("a").text  # type: ignore
            is_folder: bool = not (size_cell and size_cell.text.strip())

            full_path: str = os.path.join(save_path, name)

            if is_folder or os.path.isdir(full_path):
                os.makedirs(full_path, exist_ok=True)
                tasks.append(fetch_and_download(url + name + "/", full_path))
            else:
                tasks.append(download_file(url + name, full_path, session))

        # Await all tasks
        await asyncio.gather(*tasks)


async def download_packages():
    downloads: List[Any] = []

    for package in env.packages:
        start_url = f"{env.packages_cdn}{package['name']}@{package['version']}/"
        start_path = f"{env.weba_path}/packages/{package['name']}"  # Replace this with your desired save path
        downloads.append(fetch_and_download(start_url, start_path))

    await asyncio.gather(*downloads)
