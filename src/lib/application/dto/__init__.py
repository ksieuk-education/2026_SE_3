"""Модели запросов и ответов API."""

from lib.application.dto.auth import AuthLoginRequest, AuthRegisterRequest, AuthTokenResponse
from lib.application.dto.driver import DriverRegisterRequest, DriverResponse
from lib.application.dto.health import HealthResponse
from lib.application.dto.trip import TripAcceptRequest, TripCreateRequest, TripResponse
from lib.application.dto.user import UserCreateRequest, UserResponse

__all__ = [
    "AuthLoginRequest",
    "AuthRegisterRequest",
    "AuthTokenResponse",
    "DriverRegisterRequest",
    "DriverResponse",
    "HealthResponse",
    "TripAcceptRequest",
    "TripCreateRequest",
    "TripResponse",
    "UserCreateRequest",
    "UserResponse",
]
