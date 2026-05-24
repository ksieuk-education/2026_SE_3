"""Модели API: аутентификация."""

from pydantic import BaseModel, Field

from lib.app.domain.entities import User
from lib.application.dto.user import UserResponse


class AuthRegisterRequest(BaseModel):
    """Тело запроса: регистрация с паролем."""

    login: str = Field(min_length=1, description="Логин (уникальный)")
    password: str = Field(min_length=6, description="Пароль")
    first_name: str = Field(min_length=1, description="Имя")
    last_name: str = Field(min_length=1, description="Фамилия")


class AuthLoginRequest(BaseModel):
    """Тело запроса: вход по логину и паролю."""

    login: str = Field(min_length=1, description="Логин")
    password: str = Field(min_length=1, description="Пароль")


class AuthTokenResponse(BaseModel):
    """Ответ с JWT и данными пользователя."""

    access_token: str = Field(description="JWT access-токен")
    token_type: str = Field(default="bearer", description="Тип токена (Bearer)")
    user: UserResponse

    @classmethod
    def from_user_and_token(cls, user: User, access_token: str) -> "AuthTokenResponse":
        """Собирает ответ после регистрации или входа."""
        return cls(access_token=access_token, user=UserResponse.from_entity(user))
