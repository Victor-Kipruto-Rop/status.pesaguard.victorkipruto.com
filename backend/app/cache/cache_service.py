import json
from typing import Any

from app.cache.redis import get_redis
from app.config import get_settings

settings = get_settings()


class CacheService:
    """
    Cache-aside helper. If Redis is unreachable, callers should treat a
    failed get/set as a cache miss rather than a hard error — the status
    page must keep working even if Redis is down.
    """

    def __init__(self, prefix: str = "pesaguard"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get_json(self, key: str) -> Any | None:
        try:
            raw = await get_redis().get(self._key(key))
        except Exception:
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    async def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
        try:
            await get_redis().set(self._key(key), json.dumps(value, default=str), ex=ttl)
        except Exception:
            # Cache is best-effort; a write failure should never break a request.
            pass

    async def invalidate(self, key: str) -> None:
        try:
            await get_redis().delete(self._key(key))
        except Exception:
            pass
