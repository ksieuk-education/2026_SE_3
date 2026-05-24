"""Контракт единицы работы (транзакция + репозитории)."""

from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from lib.app.common.repositories import IDriverRepository, ITripRepository, IUserRepository


@runtime_checkable
class IUnitOfWork(Protocol):
    """
    Граница транзакции и доступ к репозиториям.

    Обычно используется как ``async with uow:``; фиксация при успешном выходе из блока.
    """

    @property
    def users(self) -> IUserRepository:
        ...

    @property
    def drivers(self) -> IDriverRepository:
        ...

    @property
    def trips(self) -> ITripRepository:
        ...

    async def commit(self) -> None:
        """Явная фиксация"""
        ...

    async def rollback(self) -> None:
        """Явный откат."""
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...
