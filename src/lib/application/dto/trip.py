"""Модели API: поездка."""

from datetime import datetime

from pydantic import BaseModel, Field

from lib.app.domain.entities import Trip, TripStatus


class TripCreateRequest(BaseModel):
    """Тело запроса: создание заказа поездки (клиент)."""

    user_id: int = Field(ge=1, description="Id заказывающего пользователя")


class TripAcceptRequest(BaseModel):
    """Тело запроса: принятие заказа водителем."""

    driver_id: int = Field(ge=1, description="Id водителя, принимающего заказ")


class TripResponse(BaseModel):
    """Поездка в ответе API."""

    id: int
    user_id: int
    driver_id: int | None
    status: TripStatus
    created_at: datetime | None = Field(default=None, description="Время создания (пояс из настроек)")

    @classmethod
    def from_entity(cls, trip: Trip) -> "TripResponse":
        """Строит ответ из доменной сущности."""
        if trip.id is None:
            msg = "у поездки должен быть id"
            raise ValueError(msg)
        return cls(
            id=trip.id,
            user_id=trip.user_id,
            driver_id=trip.driver_id,
            status=trip.status,
            created_at=trip.created_at,
        )
