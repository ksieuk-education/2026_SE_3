"""Стандартный запуск приложения"""

import asyncio

from lib.main import Settings
from lib.main.entrypoints.web import create_app, start_server


async def run() -> None:
    """Загружает настройки, собирает приложение и отдаёт его uvicorn."""
    settings = Settings()
    app = create_app(settings)
    await start_server(app, settings.api_settings)


if __name__ == "__main__":
    asyncio.run(run())
