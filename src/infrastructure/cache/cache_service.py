import redis.asyncio as redis

from ...core.config import settings
from ...core.logger import logger


class RedisCacheService:
    def __init__(self, log=None):
        self.logger = log or logger
        self._client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        if ttl:
            await self._client.set(key, value, ex=ttl)
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def ping(self) -> bool:
        try:
            return await self._client.ping()
        except Exception as e:
            self.logger.error("Redis ping failed", error=str(e))
            return False
