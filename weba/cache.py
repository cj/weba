from typing import Any, cast

from aiocache import BaseCache
from aiocache import Cache as AioCache

from .env import env

Cache = BaseCache


# FIXME: Change cast Any to actually return BaseCache without unknown type error
cache = cast(Any, AioCache.from_url(env.cache_url))  # type: ignore
