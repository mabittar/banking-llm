import json
import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import logger

SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "authorization",
    "key",
    "api-key",
}


def mask_sensitive_data(data: Any) -> Any:
    """Recursively mask sensitive keys in a dictionary or list."""
    if isinstance(data, dict):
        return {k: ("********" if k.lower() in SENSITIVE_KEYS else mask_sensitive_data(v)) for k, v in data.items()}
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # 1. Process Request
        request_body = b""
        if request.method in ["POST", "PUT", "PATCH"]:
            request_body = await request.body()

            # Restore the body for the route handler
            async def receive():
                return {"type": "http.request", "body": request_body}

            request._receive = receive

        # Log Request (Masked)
        try:
            req_json = json.loads(request_body) if request_body else {}
            masked_req = mask_sensitive_data(req_json)
            logger.info(
                "REQUEST [%s %s] Body: %s",
                request.method,
                request.url.path,
                json.dumps(masked_req),
            )
        except Exception:
            logger.info(
                "REQUEST [%s %s] (Non-JSON or empty body)",
                request.method,
                request.url.path,
            )

        # 2. Call the next handler
        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error("EXCEPTION after %.2fms: %s", process_time, str(e), exc_info=True)
            return Response(
                content=json.dumps({"detail": "Erro interno do servidor. A equipe técnica foi notificada."}),
                status_code=500,
                media_type="application/json",
            )

        # 3. Process Response
        process_time = (time.time() - start_time) * 1000

        # For logging response body, we need to consume the iterator
        # WARNING: This can be memory intensive for large files.
        # We only log JSON responses.
        if "application/json" in response.headers.get("content-type", ""):
            response_body = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))

            try:
                full_body = b"".join(response_body)
                res_json = json.loads(full_body)
                masked_res = mask_sensitive_data(res_json)
                logger.info(
                    "RESPONSE [%s %s] (%s) in %.2fms | Body: %s",
                    request.method,
                    request.url.path,
                    response.status_code,
                    process_time,
                    json.dumps(masked_res),
                )
            except Exception:
                logger.info(
                    "RESPONSE [%s %s] (%s) in %.2fms (Empty/Non-JSON)",
                    request.method,
                    request.url.path,
                    response.status_code,
                    process_time,
                )
        else:
            logger.info(
                "RESPONSE [%s %s] (%s) in %.2fms",
                request.method,
                request.url.path,
                response.status_code,
                process_time,
            )

        return response
