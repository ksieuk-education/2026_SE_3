"""Настройки приложения"""

from datetime import timedelta, timezone

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    """Настройки приложения (FastAPI и домена)"""

    wait_timeout: int = 60
    prefix: str = "/api/taxi/v1"
    title: str = "Taxi"
    version: str = "0.1.0"
    timezone_offset_hours: int = Field(
        default=3,
        ge=-12,
        le=14,
        description="Смещение относительно UTC в часах (для отображения дат в домене/API).",
    )
    timezone_name: str = Field(
        default="UTC+3",
        description="Имя для datetime.timezone (метка в repr).",
    )

    def get_timezone(self) -> timezone:
        """Часовой пояс приложения (фиксированное смещение)."""
        return timezone(
            timedelta(hours=self.timezone_offset_hours),
            name=self.timezone_name,
        )
