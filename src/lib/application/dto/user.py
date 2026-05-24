"""Модели API: пользователь."""

from pydantic import BaseModel, Field

from lib.app.domain.entities import User


class UserCreateRequest(BaseModel):
    """Тело запроса: создание пользователя."""

    login: str = Field(min_length=1, description="Логин (уникальный)")
    first_name: str = Field(min_length=1, description="Имя")
    last_name: str = Field(min_length=1, description="Фамилия")


class UserResponse(BaseModel):
    """Пользователь в ответе API."""

    id: int = Field(description="Идентификатор")
    login: str
    first_name: str
    last_name: str

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        """Строит ответ из доменной сущности."""
        if user.id is None:
            msg = "у пользователя должен быть id"
            raise ValueError(msg)
        return cls(
            id=user.id,
            login=user.login,
            first_name=user.first_name,
            last_name=user.last_name,
        )
