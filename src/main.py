from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from .chat.router import chat_router
from .core.cache import CacheProtocol
from .core.config import BaseSettings, settings
from .core.health_check import health_router
from .core.logger import logger
from .core.middleware import LoggingMiddleware
from .infrastructure.cache.cache_service import RedisCacheService


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    ) as checkpointer:
        await checkpointer.setup()
        app.state.checkpointer = checkpointer
        logger.info("Checkpointer setup complete", db=settings.DBNAME)
        yield
        logger.info("Checkpointer connection closed")


class App:
    def __init__(
        self, settings: BaseSettings, cache: CacheProtocol | None = None, lifespan=None
    ):
        self.settings = settings
        self.__app = FastAPI(**settings.set_app_attributes, lifespan=lifespan)
        self.__app.state.cache = cache
        self.__setup_middleware()
        self.__add_routes()

    def __setup_middleware(self):
        self.__app.add_middleware(LoggingMiddleware)

    def __add_routes(self):
        self.__app.include_router(router=health_router)
        self.__app.include_router(router=chat_router)

    def __call__(self) -> FastAPI:
        return self.__app


def initialize_application() -> FastAPI:
    cache = RedisCacheService()
    return App(settings=settings, cache=cache, lifespan=lifespan)()


app = initialize_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
