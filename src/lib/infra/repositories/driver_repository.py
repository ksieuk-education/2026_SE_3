"""Репозиторий водителей (PostgreSQL)."""

import asyncpg

from lib.app.common.repositories import IDriverRepository
from lib.app.domain.entities import Driver
from lib.infra.common.errors import SaveError


class DriverRepository(IDriverRepository):
    """Регистрация и чтение водителей."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(self, driver: Driver) -> Driver:
        if driver.id is not None:
            msg = "при создании водителя поле id должно быть пустым"
            raise ValueError(msg)
        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO drivers (user_id) VALUES ($1)
                RETURNING id, user_id
                """,
                driver.user_id,
            )
        except asyncpg.UniqueViolationError as exc:
            raise SaveError("ошибка сохранения водителя: дубликат или нарушение ограничений БД") from exc
        except asyncpg.ForeignKeyViolationError as exc:
            raise SaveError("ошибка сохранения водителя: дубликат или нарушение ограничений БД") from exc
        if row is None:  # pragma: no cover
            msg = "после вставки строки не получена запись"
            raise RuntimeError(msg)
        return Driver(id=row["id"], user_id=row["user_id"])

    async def get_by_id(self, driver_id: int) -> Driver | None:
        row = await self._conn.fetchrow(
            "SELECT id, user_id FROM drivers WHERE id = $1",
            driver_id,
        )
        if row is None:
            return None
        return Driver(id=row["id"], user_id=row["user_id"])

    async def get_by_user_id(self, user_id: int) -> Driver | None:
        row = await self._conn.fetchrow(
            "SELECT id, user_id FROM drivers WHERE user_id = $1",
            user_id,
        )
        if row is None:
            return None
        return Driver(id=row["id"], user_id=row["user_id"])
