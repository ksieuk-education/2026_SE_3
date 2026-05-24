"""Хеширование паролей (PBKDF2, stdlib)."""

import hashlib
import secrets


class PasswordHasher:
    """Создание и проверка хешей паролей без внешних зависимостей."""

    _iterations = 100_000
    _separator = "$"

    def hash(self, password: str) -> str:
        """Возвращает строку ``salt$hex_digest``."""
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            self._iterations,
        )
        return f"{salt}{self._separator}{digest.hex()}"

    def verify(self, password: str, stored_hash: str) -> bool:
        """Сравнивает пароль с сохранённым хешем."""
        try:
            salt, expected_hex = stored_hash.split(self._separator, maxsplit=1)
        except ValueError:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            self._iterations,
        )
        return secrets.compare_digest(digest.hex(), expected_hex)
