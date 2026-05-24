"""Общие контракты приложения."""

from lib.app.common.repositories import IDriverRepository, ITripRepository, IUserRepository
from lib.app.common.uow import IUnitOfWork

__all__ = [
    "IDriverRepository",
    "ITripRepository",
    "IUnitOfWork",
    "IUserRepository",
]
