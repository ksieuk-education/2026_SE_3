"""
Реализация UoW для PostgreSQL (asyncpg).
"""

import logging
from datetime import timezone
from types import TracebackType
from typing import Self

import asyncpg
from asyncpg.transaction import Transaction  # noqa: TC002

from lib.app.common.repositories import IDriverRepository, ITripRepository, IUserRepository
from lib.app.common.uow import IUnitOfWork
from lib.infra.repositories.driver_repository import DriverRepository
from lib.infra.repositories.trip_repository import TripRepository
from lib.infra.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class PostgresUnitOfWork(IUnitOfWork):
    """Транзакция: одно соединение и три репозитория."""

    def __init__(self, conn: asyncpg.Connection, display_tz: timezone) -> None:
        self._conn = conn
        self._transaction: Transaction | None = None
        self._users = UserRepository(conn)
        self._drivers = DriverRepository(conn)
        self._trips = TripRepository(conn, display_tz)

    @property
    def users(self) -> IUserRepository:
        return self._users

    @property
    def drivers(self) -> IDriverRepository:
        return self._drivers

    @property
    def trips(self) -> ITripRepository:
        return self._trips

    async def __aenter__(self) -> Self:
        transaction = self._conn.transaction()
        await transaction.start()
        self._transaction = transaction
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._transaction is None:
            return
        try:
            if exc_type is not None:
                logger.debug("UoW rollback из-за исключения: %s", exc_val)
                await self._transaction.rollback()
            else:
                await self._transaction.commit()
        except asyncpg.PostgresError:
            logger.exception("Ошибка PostgreSQL при завершении UoW, откат.")
            await self._transaction.rollback()
            raise

    async def commit(self) -> None:
        if self._transaction is None:
            msg = "транзакция UoW не начата"
            raise RuntimeError(msg)
        await self._transaction.commit()
        transaction = self._conn.transaction()
        await transaction.start()
        self._transaction = transaction

    async def rollback(self) -> None:
        if self._transaction is None:
            msg = "транзакция UoW не начата"
            raise RuntimeError(msg)
        await self._transaction.rollback()
        transaction = self._conn.transaction()
        await transaction.start()
        self._transaction = transaction
