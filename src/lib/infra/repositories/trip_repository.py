"""Репозиторий поездок (PostgreSQL)."""

from datetime import UTC, datetime, timezone

import asyncpg

from lib.app.common.repositories import ITripRepository
from lib.app.domain.entities import Trip, TripStatus


class TripRepository(ITripRepository):
    """Заказы поездок."""

    def __init__(self, conn: asyncpg.Connection, display_tz: timezone) -> None:
        self._conn = conn
        self._display_tz = display_tz

    def _parse_created_at(self, value: datetime | str) -> datetime:
        if isinstance(value, datetime):
            dt = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        elif value.endswith("Z"):
            dt = datetime.fromisoformat(value.removesuffix("Z")).replace(tzinfo=UTC)
        else:
            dt = datetime.fromisoformat(value)
            dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
        return dt.astimezone(self._display_tz)

    def _row_to_trip(self, row: asyncpg.Record) -> Trip:
        return Trip(
            id=row["id"],
            user_id=row["user_id"],
            driver_id=row["driver_id"],
            status=TripStatus(row["status"]),
            created_at=self._parse_created_at(row["created_at"]),
        )

    async def create(self, trip: Trip) -> Trip:
        if trip.id is not None:
            msg = "при создании поездки поле id должно быть пустым"
            raise ValueError(msg)
        row = await self._conn.fetchrow(
            """
            INSERT INTO trips (user_id, driver_id, status)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, driver_id, status, created_at
            """,
            trip.user_id,
            trip.driver_id,
            trip.status.value,
        )
        if row is None:  # pragma: no cover
            msg = "не удалось прочитать созданную поездку из базы"
            raise RuntimeError(msg)
        return self._row_to_trip(row)

    async def get_by_id(self, trip_id: int) -> Trip | None:
        row = await self._conn.fetchrow(
            """
            SELECT id, user_id, driver_id, status, created_at
            FROM trips WHERE id = $1
            """,
            trip_id,
        )
        if row is None:
            return None
        return self._row_to_trip(row)

    async def list_active(self) -> list[Trip]:
        rows = await self._conn.fetch(
            """
            SELECT id, user_id, driver_id, status, created_at FROM trips
            WHERE status IN ($1, $2)
            ORDER BY created_at DESC
            """,
            TripStatus.PENDING.value,
            TripStatus.ACTIVE.value,
        )
        return [self._row_to_trip(r) for r in rows]

    async def list_history_for_user(self, user_id: int) -> list[Trip]:
        rows = await self._conn.fetch(
            """
            SELECT id, user_id, driver_id, status, created_at FROM trips
            WHERE user_id = $1 AND status = $2
            ORDER BY created_at DESC
            """,
            user_id,
            TripStatus.COMPLETED.value,
        )
        return [self._row_to_trip(r) for r in rows]

    async def try_accept(self, trip_id: int, driver_id: int) -> Trip | None:
        row = await self._conn.fetchrow(
            """
            UPDATE trips
            SET driver_id = $1, status = $2
            WHERE id = $3 AND status = $4
            RETURNING id, user_id, driver_id, status, created_at
            """,
            driver_id,
            TripStatus.ACTIVE.value,
            trip_id,
            TripStatus.PENDING.value,
        )
        if row is None:
            return None
        return self._row_to_trip(row)

    async def try_complete(self, trip_id: int) -> Trip | None:
        row = await self._conn.fetchrow(
            """
            UPDATE trips SET status = $1
            WHERE id = $2 AND status = $3
            RETURNING id, user_id, driver_id, status, created_at
            """,
            TripStatus.COMPLETED.value,
            trip_id,
            TripStatus.ACTIVE.value,
        )
        if row is None:
            return None
        return self._row_to_trip(row)
