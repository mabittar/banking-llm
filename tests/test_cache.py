import pytest

from tests import FakeCache


@pytest.mark.asyncio
async def test_set_and_get(fake_cache: FakeCache):
    await fake_cache.set("key1", "value1")
    result = await fake_cache.get("key1")
    assert result == "value1"


@pytest.mark.asyncio
async def test_get_missing_key(fake_cache: FakeCache):
    result = await fake_cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_delete(fake_cache: FakeCache):
    await fake_cache.set("key1", "value1")
    await fake_cache.delete("key1")
    result = await fake_cache.get("key1")
    assert result is None


@pytest.mark.asyncio
async def test_delete_missing_key(fake_cache: FakeCache):
    await fake_cache.delete("nonexistent")  # should not raise


@pytest.mark.asyncio
async def test_ping(fake_cache: FakeCache):
    assert await fake_cache.ping() is True


@pytest.mark.asyncio
async def test_ping_failure(fake_cache: FakeCache):
    fake_cache._ping_response = False
    assert await fake_cache.ping() is False


@pytest.mark.asyncio
async def test_overwrite_value(fake_cache: FakeCache):
    await fake_cache.set("key1", "v1")
    await fake_cache.set("key1", "v2")
    assert await fake_cache.get("key1") == "v2"
