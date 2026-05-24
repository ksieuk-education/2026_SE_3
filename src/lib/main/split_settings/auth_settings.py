"""Настройки JWT-аутентификации."""

from pydantic import BaseModel, Field


class AuthSettings(BaseModel):
    """Параметры выдачи и проверки JWT."""

    jwt_secret: str = Field(
        default="change-me-in-production",
        min_length=16,
        description="Секрет для подписи JWT (переопределить через конфиг или env).",
    )
    jwt_algorithm: str = Field(default="HS256", description="Алгоритм подписи JWT.")
    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        description="Срок жизни access-токена в минутах.",
    )
