"""Проверка JWT для защищённых маршрутов."""

import re
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from lib.application.auth.errors import AuthenticationError
from lib.application.auth.jwt_token_service import JwtTokenService

RequestHandler = Callable[[Request], Awaitable[Response]]

_TRIPS_HISTORY_PATTERN = re.compile(r"^/users/\d+/trips/history$")


def is_protected_route(*, method: str, path_without_prefix: str) -> bool:
    """
    Определяет, требует ли маршрут Bearer-токен.

    Защищены: POST /drivers, POST /trips, GET /users/{id}/trips/history.
    """
    if method == "POST" and path_without_prefix == "/drivers":
        return True
    if method == "POST" and path_without_prefix == "/trips":
        return True
    return method == "GET" and _TRIPS_HISTORY_PATTERN.match(path_without_prefix) is not None


class _AuthMiddleware:
    """HTTP-middleware: проверка Bearer JWT для защищённых маршрутов."""

    def __init__(self, jwt_token_service: JwtTokenService, api_prefix: str) -> None:
        self._jwt_token_service = jwt_token_service
        self._api_prefix = api_prefix.rstrip("/")

    async def __call__(self, request: Request, call_next: RequestHandler) -> Response:
        path = request.url.path
        relative_path = path.removeprefix(self._api_prefix) if path.startswith(self._api_prefix) else path

        if is_protected_route(method=request.method, path_without_prefix=relative_path):
            auth_header = request.headers.get("Authorization")
            if auth_header is None or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "требуется заголовок Authorization: Bearer <token>"},
                )
            token = auth_header.removeprefix("Bearer ").strip()
            if not token:
                return JSONResponse(status_code=401, content={"detail": "пустой Bearer-токен"})
            try:
                payload = self._jwt_token_service.decode_access_token(token)
            except AuthenticationError as exc:
                return JSONResponse(status_code=401, content={"detail": str(exc)})
            request.state.user_id = payload["user_id"]
            request.state.auth_login = payload.get("login")

        return await call_next(request)


def register_auth_middleware(
    app: FastAPI,
    *,
    jwt_token_service: JwtTokenService,
    api_prefix: str,
) -> None:
    """Регистрирует HTTP-middleware проверки JWT на приложении FastAPI."""
    app.middleware("http")(_AuthMiddleware(jwt_token_service, api_prefix))
