"""Сборка контейнера Dishka."""

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider

from lib.main.ioc.providers import AppProvider, InfraProvider
from lib.main.settings import Settings


def create_async_container(settings: Settings) -> AsyncContainer:
    """Создаёт async-контейнер для HTTP-сервиса."""
    return make_async_container(
        InfraProvider(),
        AppProvider(),
        FastapiProvider(),
        context={Settings: settings},
    )
