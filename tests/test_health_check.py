import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.health_check import health_router
from tests import FakeCache


def _create_app(cache) -> FastAPI:
    app = FastAPI()
    app.state.cache = cache
    app.include_router(health_router)
    return app


@pytest.fixture
def client_with_cache(fake_cache: FakeCache):
    app = _create_app(fake_cache)
    return TestClient(app)


@pytest.fixture
def client_without_cache():
    app = _create_app(None)
    return TestClient(app)


def test_health_check_redis_up(client_with_cache: TestClient):
    response = client_with_cache.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["services"]["redis"] == "up"


def test_health_check_redis_down(fake_cache: FakeCache):
    fake_cache._ping_response = False
    app = _create_app(fake_cache)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["services"]["redis"] == "down"


def test_health_check_no_cache(client_without_cache: TestClient):
    response = client_without_cache.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["services"]["redis"] == "not_configured"
