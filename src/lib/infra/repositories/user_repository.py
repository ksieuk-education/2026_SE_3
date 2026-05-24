"""Репозиторий пользователей (PostgreSQL)."""

import asyncpg

from lib.app.common.repositories import IUserRepository
from lib.app.domain.entities import User
from lib.infra.common.errors import SaveError


class UserRepository(IUserRepository):
    """CRUD пользователей в одной транзакции PostgreSQL."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(self, user: User) -> User:
        if user.id is not None:
            msg = "при создании пользователя поле id должно быть пустым"
            raise ValueError(msg)
        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO users (login, first_name, last_name, password_hash)
                VALUES ($1, $2, $3, $4)
                RETURNING id, login, first_name, last_name, password_hash
                """,
                user.login,
                user.first_name,
                user.last_name,
                user.password_hash,
            )
        except asyncpg.UniqueViolationError as exc:
            raise SaveError("ошибка сохранения пользователя: дубликат или нарушение ограничений БД") from exc
        if row is None:  # pragma: no cover
            msg = "после вставки строки не получена запись"
            raise RuntimeError(msg)
        return User(
            id=row["id"],
            login=row["login"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            password_hash=row["password_hash"],
        )

    async def get_by_id(self, user_id: int) -> User | None:
        row = await self._conn.fetchrow(
            "SELECT id, login, first_name, last_name, password_hash FROM users WHERE id = $1",
            user_id,
        )
        if row is None:
            return None
        return User(
            id=row["id"],
            login=row["login"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            password_hash=row["password_hash"],
        )

    async def get_by_login(self, login: str) -> User | None:
        row = await self._conn.fetchrow(
            """
            SELECT id, login, first_name, last_name, password_hash
            FROM users WHERE lower(login) = lower($1)
            """,
            login,
        )
        if row is None:
            return None
        return User(
            id=row["id"],
            login=row["login"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            password_hash=row["password_hash"],
        )

    async def search_by_name_mask(self, pattern: str) -> list[User]:
        like = pattern if "%" in pattern or "_" in pattern else f"%{pattern}%"
        rows = await self._conn.fetch(
            """
            SELECT id, login, first_name, last_name, password_hash FROM users
            WHERE (first_name || ' ' || last_name) ILIKE $1
            ORDER BY last_name, first_name
            """,
            like,
        )
        return [
            User(
                id=r["id"],
                login=r["login"],
                first_name=r["first_name"],
                last_name=r["last_name"],
                password_hash=r["password_hash"],
            )
            for r in rows
        ]
