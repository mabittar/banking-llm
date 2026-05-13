from src.core.cache import CacheProtocol


class FakeCache:
    """In-memory cache implementing CacheProtocol for testing."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._ping_response: bool = True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def ping(self) -> bool:
        return self._ping_response


assert isinstance(FakeCache(), CacheProtocol)
