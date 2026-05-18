from langgraph.checkpoint.memory import MemorySaver
import pytest

from tests import FakeCache


@pytest.fixture
def fake_cache() -> FakeCache:
    return FakeCache()


@pytest.fixture
def fake_checkpointer() -> MemorySaver:
    return MemorySaver()
