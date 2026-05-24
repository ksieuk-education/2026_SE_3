"""Модели API: водитель."""

from pydantic import BaseModel, Field

from lib.app.domain.entities import Driver


class DriverRegisterRequest(BaseModel):
    """Тело запроса: регистрация водителя по учётной записи пользователя."""

    user_id: int = Field(ge=1, description="Id пользователя, который становится водителем")


class DriverResponse(BaseModel):
    """Водитель в ответе API."""

    id: int = Field(description="Идентификатор водителя")
    user_id: int = Field(description="Связанный пользователь")

    @classmethod
    def from_entity(cls, driver: Driver) -> "DriverResponse":
        """Строит ответ из доменной сущности."""
        if driver.id is None:
            msg = "у водителя должен быть id"
            raise ValueError(msg)
        return cls(id=driver.id, user_id=driver.user_id)
