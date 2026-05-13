from unittest.mock import MagicMock, patch

import pytest

from tests import FakeCache


@pytest.fixture
def mock_settings():
    with patch("src.infrastructure.banking.banking_auth.settings") as mock:
        mock.BANKING_BASE_URL = "https://banking.test"
        mock.CLIENT_ID = "test-client"
        mock.REALM_NAME = "test-realm"
        mock.JWT_SECRET = "test-secret"
        yield mock


@pytest.fixture
def mock_jwt_encode():
    with patch("src.infrastructure.banking.banking_auth.jwt.encode", return_value="signed-jwt") as mock:
        yield mock


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "accessToken": "token-abc-123",
        "expiresIn": 1800,
    }
    response.raise_for_status = MagicMock()
    return response


@pytest.mark.asyncio
async def test_login_persists_token_in_cache(fake_cache: FakeCache, mock_settings, mock_jwt_encode, mock_response):
    from src.infrastructure.banking.banking_auth import BankingAuth

    auth = BankingAuth(cache_service=fake_cache)
    auth.client = MagicMock()
    auth.client.post = MagicMock(return_value=mock_response)

    await auth.login()

    assert auth.token == "token-abc-123"
    cached = await fake_cache.get("banking:access_token")
    assert cached == "token-abc-123"


@pytest.mark.asyncio
async def test_get_valid_token_returns_from_cache(fake_cache: FakeCache, mock_settings):
    from src.infrastructure.banking.banking_auth import BankingAuth

    await fake_cache.set("banking:access_token", "cached-token-xyz")

    auth = BankingAuth(cache_service=fake_cache)
    token = await auth.get_valid_token()

    assert token == "cached-token-xyz"


@pytest.mark.asyncio
async def test_get_valid_token_falls_back_to_login_when_cache_empty(
    fake_cache: FakeCache, mock_settings, mock_jwt_encode, mock_response
):
    from src.infrastructure.banking.banking_auth import BankingAuth

    auth = BankingAuth(cache_service=fake_cache)
    auth.client = MagicMock()
    auth.client.post = MagicMock(return_value=mock_response)

    token = await auth.get_valid_token()

    assert token == "token-abc-123"
    cached = await fake_cache.get("banking:access_token")
    assert cached == "token-abc-123"


@pytest.mark.asyncio
async def test_get_valid_token_works_without_cache(mock_settings, mock_jwt_encode, mock_response):
    from src.infrastructure.banking.banking_auth import BankingAuth

    auth = BankingAuth(cache_service=None)
    auth.client = MagicMock()
    auth.client.post = MagicMock(return_value=mock_response)

    token = await auth.get_valid_token()

    assert token == "token-abc-123"
