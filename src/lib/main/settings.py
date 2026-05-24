"""Настройки проекта"""

from typing import Any

import pydantic

from lib.main.split_settings import LoggingSettings
from lib.main.split_settings.api_settings import ApiSettings
from lib.main.split_settings.app_settings import AppSettings
from lib.main.split_settings.auth_settings import AuthSettings
from lib.main.split_settings.database_settings import DatabaseSettings
from lib.main.split_settings.utils import BaseSettings


class Settings(BaseSettings):
    """Настройки проекта"""

    use_config_yml: bool = True

    app_settings: AppSettings = pydantic.Field(default_factory=AppSettings)
    auth_settings: AuthSettings = pydantic.Field(default_factory=AuthSettings)
    api_settings: ApiSettings = pydantic.Field(default_factory=ApiSettings)
    database_settings: DatabaseSettings = pydantic.Field(default_factory=DatabaseSettings)
    logging_settings: LoggingSettings = pydantic.Field(default_factory=LoggingSettings)

    def model_post_init(self, /, __context: Any) -> None:  # noqa: ANN401
        """Пост инициализация"""
        self.logging_settings.init_logging()
        return super().model_post_init(__context)
