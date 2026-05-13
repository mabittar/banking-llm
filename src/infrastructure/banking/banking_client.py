from urllib.parse import quote

from ...core.config import settings
from ...core.logger import logger
from .banking_auth import BankingAuth
from ..dto import ListKeysDTOResponse, ReadKeysResponseDTO


class BankingClient:
    def __init__(self, log=None, cache_service=None):
        self.logger = log or logger
        self.auth = BankingAuth(log=self.logger, cache_service=cache_service)
        self.base_url = settings.BANKING_BASE_URL
        self.default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Connection": "close",
        }
        self.client = self.auth.client

    def __url(self, url: str) -> str:
        """
        Mount url with default url.
        """

        return f"{self.base_url}{url}"

    async def build_headers(self):
        headers = self.default_headers.copy()
        headers["Authorization"] = f"Bearer {await self.auth.get_valid_token()}"
        headers["client-id"] = settings.CLIENT_ID
        return headers

    async def list_active_pix_keys(
        self, fin_account_id: str, filter: str | None = "?status=ACTIVE"
    ) -> ListKeysDTOResponse:
        path = f"/api/v1/pix/{fin_account_id}/keys"
        if filter:
            path += f"{filter}"
        url = self.__url(path)
        headers = await self.build_headers()
        response = self.client.get(url, headers=headers)
        self.logger.debug(f"List Active Pix Keys status Code: {response.status_code}")
        response.raise_for_status()
        body = response.json()
        self.logger.info(f"Active Pix Keys for Fin Account {fin_account_id}: {body}")
        return ListKeysDTOResponse(**body)

    async def read_pix_key(self, pix_key: str, fin_account_id: str) -> ReadKeysResponseDTO:
        path = f"/api/v1/pix/{fin_account_id}/key/{quote(pix_key, safe='')}"
        url = self.__url(path)
        headers = await self.build_headers()
        response = self.client.get(url, headers=headers)
        self.logger.debug(f"Read Pix Key status Code: {response.status_code}")
        response.raise_for_status()
        body = response.json()
        self.logger.info(f"Read Pix Key response for key {pix_key} - e2e: {body.get('endToEndId')}")
        return ReadKeysResponseDTO(**body)
