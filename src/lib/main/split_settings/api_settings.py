"""Настройки API"""

import pydantic


class ApiSettings(pydantic.BaseModel):
    """Настройки API"""

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
