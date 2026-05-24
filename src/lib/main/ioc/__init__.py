"""IOC (Dishka)."""

from lib.main.ioc.di import create_async_container
from lib.main.ioc.providers import AppProvider, InfraProvider

__all__ = ["AppProvider", "InfraProvider", "create_async_container"]
