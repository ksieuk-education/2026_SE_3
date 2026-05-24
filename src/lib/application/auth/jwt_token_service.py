"""Выдача и проверка JWT access-токенов."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from lib.application.auth.errors import AuthenticationError
from lib.main.split_settings.auth_settings import AuthSettings


class JwtTokenService:
    """Подписывает и декодирует JWT с идентификатором пользователя."""

    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings

    def create_access_token(self, *, user_id: int, login: str) -> str:
        """Формирует Bearer-токен для пользователя."""
        expire = datetime.now(tz=UTC) + timedelta(minutes=self._settings.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "login": login,
            "exp": expire,
        }
        return jwt.encode(
            payload,
            self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
        )

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """
        Проверяет подпись и срок действия токена.

        :raises AuthenticationError: если токен недействителен
        """
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret,
                algorithms=[self._settings.jwt_algorithm],
            )
        except jwt.PyJWTError as exc:
            msg = "недействительный или просроченный токен"
            raise AuthenticationError(msg) from exc
        sub = payload.get("sub")
        if sub is None:
            msg = "в токене отсутствует идентификатор пользователя"
            raise AuthenticationError(msg)
        try:
            user_id = int(sub)
        except (TypeError, ValueError) as exc:
            msg = "некорректный идентификатор пользователя в токене"
            raise AuthenticationError(msg) from exc
        return {"user_id": user_id, "login": payload.get("login")}
