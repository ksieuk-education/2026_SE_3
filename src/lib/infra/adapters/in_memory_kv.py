"""In-memory key-value хранилище в процессе Python"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

TTL_KEY_MISSING = -2
TTL_NO_EXPIRE = -1


@dataclass(frozen=True, slots=True)
class _Entry:
    """Запись значения с опциональным сроком жизни."""

    value: str
    expires_at: float | None


class InMemoryKVStore:
    """
    Асинхронное KV-хранилище в памяти одного процесса.

    Потокобезопасно относительно конкурентных ``async``-задач (один ``asyncio.Lock``).
    Для срока жизни используется ``time.monotonic()``.
    """

    def __init__(self) -> None:
        self._data: dict[str, _Entry] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _expired(entry: _Entry) -> bool:
        if entry.expires_at is None:
            return False
        return time.monotonic() >= entry.expires_at

    def _pop_if_expired(self, key: str, entry: _Entry) -> bool:
        """Удаляет просроченный ключ. Возвращает True, если ключ удалён как просроченный."""
        if self._expired(entry):
            del self._data[key]
            return True
        return False

    async def get(self, key: str) -> str | None:
        """Возвращает строковое значение или ``None``, если ключа нет или срок истёк."""
        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if self._pop_if_expired(key, entry):
                return None
            return entry.value

    async def set(self, key: str, value: str, *, ex: int | None = None) -> None:
        """
        Сохраняет значение.

        :param key: ключ
        :param value: строка
        :param ex: время жизни в секундах
        """
        expires_at: float | None = None
        if ex is not None:
            if ex <= 0:
                msg = "параметр времени жизни ex должен быть положительным"
                raise ValueError(msg)
            expires_at = time.monotonic() + float(ex)

        async with self._lock:
            self._data[key] = _Entry(value=value, expires_at=expires_at)

    async def delete(self, *keys: str) -> int:
        """Удаляет ключи. Число удалённых существовавших и непросроченных ключей"""
        async with self._lock:
            removed = 0
            for key in keys:
                entry = self._data.get(key)
                if entry is None:
                    continue
                if self._expired(entry):
                    del self._data[key]
                    continue
                del self._data[key]
                removed += 1
            return removed

    async def exists(self, key: str) -> bool:
        """Проверяет наличие ключа с неистёкшим TTL."""
        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            return not self._pop_if_expired(key, entry)

    async def ttl(self, key: str) -> int:
        """
        Оставшееся время жизни в секундах (округление вниз).
        """
        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return TTL_KEY_MISSING
            if self._pop_if_expired(key, entry):
                return TTL_KEY_MISSING
            if entry.expires_at is None:
                return TTL_NO_EXPIRE
            remaining = entry.expires_at - time.monotonic()
            return max(0, int(remaining))

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Задаёт TTL существующему ключу.

        :returns: False, если ключа нет или он просрочен (и будет удалён)
        """
        if seconds <= 0:
            msg = "число секунд должно быть положительным"
            raise ValueError(msg)

        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            if self._pop_if_expired(key, entry):
                return False
            self._data[key] = _Entry(
                value=entry.value,
                expires_at=time.monotonic() + float(seconds),
            )
            return True

    async def incr(self, key: str, *, delta: int = 1) -> int:
        """
        Инкремент целого, хранимого как десятичная строка.

        Отсутствующий ключ создаётся со значением 0 перед увеличением.
        """
        async with self._lock:
            entry = self._data.get(key)
            if entry is not None and self._expired(entry):
                del self._data[key]
                entry = None

            if entry is None:
                n = delta
                self._data[key] = _Entry(value=str(n), expires_at=None)
                return n

            try:
                n = int(entry.value) + delta
            except ValueError as exc:
                msg = "значение не является целым числом"
                raise ValueError(msg) from exc
            self._data[key] = _Entry(value=str(n), expires_at=entry.expires_at)
            return n

    async def flushdb(self) -> None:
        """Очищает всё хранилище."""
        async with self._lock:
            self._data.clear()
