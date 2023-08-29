from aiocache import BaseCache
from aiocache import Cache as AioCache

from .env import env

Cache = BaseCache

cache = AioCache.from_url(env.cache_url)  # type: ignore
