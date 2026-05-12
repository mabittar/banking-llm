from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

health_router = APIRouter(tags=["Health Checker"])


@health_router.get(
    "/health",
    response_class=JSONResponse,
    name="api-health:check-health",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """Simple health-check endpoint."""
    try:
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
