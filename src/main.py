from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from .chat.router import chat_router
from .core.cache import CacheProtocol
from .core.config import BaseSettings, settings
from .core.health_check import health_router
from .core.logger import logger
from .core.middleware import LoggingMiddleware
from .core.observability import setup as setup_telemetry
from .core.observability.fastapi_instrumentation import instrument_fastapi_app
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
        self.__app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.__app.add_middleware(LoggingMiddleware)

    def __add_routes(self):
        self.__app.include_router(router=health_router)
        self.__app.include_router(router=chat_router)

    def __call__(self) -> FastAPI:
        return self.__app


def initialize_application() -> FastAPI:
    # Telemetry must be bootstrapped before any instrumented component is built,
    # so providers exist when the FastAPI app and IO clients are wired.
    setup_telemetry(settings)
    cache = RedisCacheService()
    app = App(settings=settings, cache=cache, lifespan=lifespan)()
    instrument_fastapi_app(app)
    return app


app = initialize_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
