"""Контракты репозиториев."""

from typing import Protocol, runtime_checkable

from lib.app.domain.entities import Driver, Trip, User


@runtime_checkable
class IUserRepository(Protocol):
    """Доступ к пользователям."""

    async def create(self, user: User) -> User:
        """Создаёт пользователя, возвращает сущность с заполненным ``id``."""
        ...

    async def get_by_id(self, user_id: int) -> User | None:
        """Находит пользователя по первичному ключу."""
        ...

    async def get_by_login(self, login: str) -> User | None:
        """Находит пользователя по логину (без учёта регистра)."""
        ...

    async def search_by_name_mask(self, pattern: str) -> list[User]:
        """
        Поиск по подстроке в конкатенации имени и фамилии (SQL ``LIKE``).

        :param pattern: шаблон с ``%`` / ``_``, напр. ``%Иван%``
        """
        ...


@runtime_checkable
class IDriverRepository(Protocol):
    """Доступ к водителям."""

    async def create(self, driver: Driver) -> Driver:
        """Регистрирует водителя, возвращает сущность с ``id``."""
        ...

    async def get_by_id(self, driver_id: int) -> Driver | None:
        ...

    async def get_by_user_id(self, user_id: int) -> Driver | None:
        ...


@runtime_checkable
class ITripRepository(Protocol):
    """Доступ к поездкам."""

    async def create(self, trip: Trip) -> Trip:
        """Создаёт заказ (обычно в статусе ``pending``)."""
        ...

    async def get_by_id(self, trip_id: int) -> Trip | None:
        ...

    async def list_active(self) -> list[Trip]:
        """Заказы в работе: ``pending`` и ``active``."""
        ...

    async def list_history_for_user(self, user_id: int) -> list[Trip]:
        """Завершённые поездки пользователя, новые первыми."""
        ...

    async def try_accept(self, trip_id: int, driver_id: int) -> Trip | None:
        """
        Водитель принимает заказ: обновляет только если статус ``pending``.

        :returns: обновлённая поездка или ``None``, если не удалось
        """
        ...

    async def try_complete(self, trip_id: int) -> Trip | None:
        """
        Завершает поездку, если она ``active``.

        :returns: обновлённая поездка или ``None``
        """
        ...
