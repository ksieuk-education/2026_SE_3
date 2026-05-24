"""DTO для проверки доступности API."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Ответ health-check."""

    status: str = Field(description="Состояние сервиса")
    title: str = Field(description="Название API")
    version: str = Field(description="Версия API")
