"""Провайдеры Dishka: приложение и инфраструктура."""

from collections.abc import AsyncIterator

import asyncpg
from dishka import Provider, Scope, from_context, provide  # pyright: ignore[reportUnknownVariableType]

from lib.app.common.uow import IUnitOfWork
from lib.application.auth.auth_service import AuthService
from lib.application.auth.jwt_token_service import JwtTokenService
from lib.application.auth.password_hasher import PasswordHasher
from lib.infra.common.uow import PostgresUnitOfWork
from lib.main.settings import Settings
from lib.main.split_settings.auth_settings import AuthSettings


class InfraProvider(Provider):
    """Соединение REQUEST-scoped и транзакция UoW."""

    @provide(scope=Scope.REQUEST)
    async def postgres_connection(self, settings: Settings) -> AsyncIterator[asyncpg.Connection]:
        conn = await asyncpg.connect(settings.database_settings.build_dsn())
        try:
            yield conn
        finally:
            await conn.close()

    @provide(scope=Scope.REQUEST)
    async def unit_of_work(self, conn: asyncpg.Connection, settings: Settings) -> AsyncIterator[IUnitOfWork]:
        display_tz = settings.app_settings.get_timezone()
        async with PostgresUnitOfWork(conn, display_tz) as uow:
            yield uow


class AppProvider(Provider):
    """Базовые зависимости приложения (APP scope)."""

    settings = from_context(provides=Settings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def auth_settings(self, settings: Settings) -> AuthSettings:
        return settings.auth_settings

    @provide(scope=Scope.APP)
    def password_hasher(self) -> PasswordHasher:
        return PasswordHasher()

    @provide(scope=Scope.APP)
    def jwt_token_service(self, auth_settings: AuthSettings) -> JwtTokenService:
        return JwtTokenService(auth_settings)

    @provide(scope=Scope.REQUEST)
    def auth_service(
        self,
        uow: IUnitOfWork,
        password_hasher: PasswordHasher,
        jwt_token_service: JwtTokenService,
    ) -> AuthService:
        return AuthService(uow, password_hasher, jwt_token_service)
