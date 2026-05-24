"""HTTP-приложение FastAPI."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from lib.application.auth.jwt_token_service import JwtTokenService
from lib.main.ioc.di import create_async_container
from lib.main.settings import Settings
from lib.main.split_settings.api_settings import ApiSettings
from lib.present.api.middleware.auth_middleware import register_auth_middleware
from lib.present.api.routes.auth_route import router_auth
from lib.present.api.routes.health_route import router_health
from lib.present.api.routes.taxi_route import router_taxi

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Собирает приложение: lifespan контейнера Dishka, OpenAPI из метаданных настроек.

    :param settings: явные настройки; иначе загружаются через ``Settings()``.
    """
    cfg = settings or Settings()
    container = create_async_container(cfg)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        yield
        await app.state.dishka_container.close()

    app = FastAPI(
        title=cfg.app_settings.title,
        version=cfg.app_settings.version,
        docs_url=f"{cfg.app_settings.prefix}/docs",
        redoc_url=f"{cfg.app_settings.prefix}/redoc",
        openapi_url=f"{cfg.app_settings.prefix}/openapi.json",
        lifespan=lifespan,
    )
    setup_dishka(container=container, app=app)
    jwt_service = JwtTokenService(cfg.auth_settings)
    register_auth_middleware(
        app,
        jwt_token_service=jwt_service,
        api_prefix=cfg.app_settings.prefix,
    )
    app.include_router(router_health, prefix=cfg.app_settings.prefix)
    app.include_router(router_auth, prefix=cfg.app_settings.prefix)
    app.include_router(router_taxi, prefix=cfg.app_settings.prefix)
    return app


async def start_server(app: FastAPI, api_settings: ApiSettings) -> None:
    """Запускает ASGI-сервер uvicorn до остановки процесса."""
    try:
        config = uvicorn.Config(
            app=app,
            host=api_settings.host,
            port=api_settings.port,
        )
        server = uvicorn.Server(config)
        await server.serve()
    except BaseException:
        logger.exception("не удалось запустить FastAPI")
        raise
