from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from .cache import CacheProtocol

health_router = APIRouter(tags=["Health Checker"])


@health_router.get(
    "/health",
    response_class=JSONResponse,
    name="api-health:check-health",
    status_code=status.HTTP_200_OK,
)
async def health_check(request: Request):
    """Health-check endpoint with dependency status."""
    services: dict[str, str] = {}
    overall_status = "ok"

    cache: CacheProtocol | None = getattr(request.app.state, "cache", None)
    if cache:
        try:
            redis_ok = await cache.ping()
            services["redis"] = "up" if redis_ok else "down"
            if not redis_ok:
                overall_status = "degraded"
        except Exception as e:
            services["redis"] = "down"
            services["redis_error"] = str(e)
            overall_status = "degraded"
    else:
        services["redis"] = "not_configured"

    checkpointer = getattr(request.app.state, "checkpointer", None)
    if checkpointer:
        try:
            async with checkpointer.conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
            psql_ok = True
            services["postgresql"] = "up" if psql_ok else "down"
            if not psql_ok:
                overall_status = "degraded"
        except Exception as e:
            services["postgresql"] = "down"
            services["postgresql_error"] = str(e)
            overall_status = "degraded"
    else:
        services["postgresql"] = "not_configured"

    http_status = status.HTTP_200_OK if overall_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        content={"status": overall_status, "services": services},
        status_code=http_status,
    )
