"""Сущности: пользователь, водитель, поездка."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TripStatus(StrEnum):
    """Статус заказа поездки."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass(slots=True)
class User:
    """Пользователь (клиент)."""

    id: int | None
    login: str
    first_name: str
    last_name: str
    password_hash: str = ""


@dataclass(slots=True)
class Driver:
    """Водитель, привязанный к учётной записи пользователя."""

    id: int | None
    user_id: int


@dataclass(slots=True)
class Trip:
    """Поездка (заказ)."""

    id: int | None
    user_id: int
    driver_id: int | None
    status: TripStatus
    created_at: datetime | None = None
