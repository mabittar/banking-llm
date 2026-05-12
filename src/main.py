"""
FastAPI application – exposes the LangChain chain as an HTTP endpoint.
"""

from fastapi import FastAPI

from src.core.config import BaseSettings, settings

from .chat.router import chat_router
from .core.health_check import health_router
from .core.middleware import LoggingMiddleware


class App:
    """Main application class."""

    def __init__(self, settings: BaseSettings):
        self.settings = settings
        self.__app = FastAPI(**settings.set_app_attributes)
        self.__setup_middleware()
        self.__add_routes()

    def __setup_middleware(self):
        # ── Middleware ─────────────────────────────────────────────────────
        self.__app.add_middleware(LoggingMiddleware)

    def __add_routes(self):
        # ── Routes ───────────────────────────────────────────────────────────
        self.__app.include_router(router=health_router)
        self.__app.include_router(router=chat_router)

    def __call__(self) -> FastAPI:
        return self.__app


def initialize_application() -> FastAPI:
    return App(settings=settings)()


app = initialize_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
