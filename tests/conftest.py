import pytest

from tests import FakeCache


@pytest.fixture
def fake_cache() -> FakeCache:
    return FakeCache()
