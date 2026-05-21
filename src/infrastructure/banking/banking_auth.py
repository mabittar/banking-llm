import time
from datetime import datetime
from uuid import uuid4

import jwt
import pytz
import requests

from ...core.config import settings
from ...core.logger import logger

tz = pytz.timezone("America/Sao_Paulo")
now = datetime.now(tz=tz)


class BankingAuth:
    def __init__(self, log=None, cache_service=None):
        self.logger = log or logger
        self.cache_service = cache_service
        self.host = settings.BANKING_BASE_URL
        self.default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        session = requests.Session()
        session.verify = False
        self.client = session
        self.token = None
        self.client_id = settings.CLIENT_ID
        self.jwt_secret = settings.JWT_SECRET
        self.token_expiration_time = 0

    def __url(self, url: str) -> str:
        return f"{self.host}{url}"

    async def login(self):
        header = {
            "alg": "ES512",
            "typ": "JWT",
        }
        time_now = int(time.time())
        jwt_signed_data = {
            "iat": time_now,
            "exp": time_now + (1000 * 60 * 60 * 24 * 3),  # 3 days
            "aud": f"https://keycloak.example.com/realms/{settings.REALM_NAME}/protocol/openid-connect/token",
            "iss": self.client_id,
            "sub": self.client_id,
            "jti": str(uuid4()),
        }
        jwt_signed = jwt.encode(
            jwt_signed_data, self.jwt_secret, algorithm=header.get("alg")
        )
        try:
            path = "/api/v1/auth/token"
            url = self.__url(path)
            body = {"clientId": self.client_id, "clientAssertion": jwt_signed}
            response = self.client.post(url=url, json=body)
            self.logger.debug(f"Authorization status Code: {response.status_code}")
            response.raise_for_status()
            json_body = response.json()
            self.token = json_body.get("accessToken")
            expires_in = json_body.get("expiresIn", 3600)
            self.token_expiration_time = time.time() + expires_in

            if self.cache_service:
                await self.cache_service.set(
                    "banking:access_token", self.token, ttl=expires_in
                )
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            raise e

    async def get_valid_token(self, retries=0):
        if self.cache_service:
            cached = await self.cache_service.get("banking:access_token")
            if cached:
                self.token = cached
                return self.token

        if self.token and time.time() < self.token_expiration_time:
            return self.token

        self.logger.debug("Token expired or not available, acquiring a new one...")
        try:
            await self.login()
            return self.token
        except Exception as e:
            self.logger.error(f"Failed to acquire a new token: {e}")
            if retries < 3:
                self.logger.debug(f"Retrying to acquire token... Attempt {retries + 1}")
                return await self.get_valid_token(retries + 1)
            else:
                raise Exception(
                    "Failed to acquire token after multiple attempts."
                ) from e
