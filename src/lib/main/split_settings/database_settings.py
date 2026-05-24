"""Настройки базы данных."""

from urllib.parse import quote_plus

from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    """Параметры подключения к PostgreSQL."""

    host: str = Field(default="localhost", description="Хост PostgreSQL.")
    port: int = Field(default=5432, ge=1, le=65535, description="Порт PostgreSQL.")
    database: str = Field(default="taxidb", description="Имя базы данных.")
    user: str = Field(default="user", description="Пользователь БД.")
    password: str = Field(default="taxipass", description="Пароль пользователя БД.")

    def build_dsn(self) -> str:
        """Строка подключения для asyncpg."""
        safe_password = quote_plus(self.password)
        return f"postgresql://{self.user}:{safe_password}@{self.host}:{self.port}/{self.database}"
