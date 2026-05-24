"""Сценарии регистрации и входа."""

from lib.app.common.uow import IUnitOfWork
from lib.app.domain.entities import User
from lib.application.auth.errors import AuthenticationError
from lib.application.auth.jwt_token_service import JwtTokenService
from lib.application.auth.password_hasher import PasswordHasher


class AuthService:
    """Регистрация пользователя с паролем и выдача JWT при входе."""

    def __init__(
        self,
        uow: IUnitOfWork,
        password_hasher: PasswordHasher,
        jwt_token_service: JwtTokenService,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._jwt_token_service = jwt_token_service

    async def register(
        self,
        *,
        login: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> tuple[User, str]:
        """
        Создаёт пользователя с хешем пароля и возвращает access-токен.

        :raises SaveError: при конфликте логина
        """
        password_hash = self._password_hasher.hash(password)
        user = User(
            None,
            login.strip(),
            first_name.strip(),
            last_name.strip(),
            password_hash=password_hash,
        )
        created = await self._uow.users.create(user)
        if created.id is None:
            msg = "после регистрации у пользователя должен быть id"
            raise RuntimeError(msg)
        token = self._jwt_token_service.create_access_token(user_id=created.id, login=created.login)
        return created, token

    async def login(self, *, login: str, password: str) -> tuple[User, str]:
        """
        Проверяет пароль и возвращает access-токен.

        :raises AuthenticationError: если логин или пароль неверны
        """
        user = await self._uow.users.get_by_login(login.strip())
        if user is None or not user.password_hash:
            msg = "неверный логин или пароль"
            raise AuthenticationError(msg)
        if not self._password_hasher.verify(password, user.password_hash):
            msg = "неверный логин или пароль"
            raise AuthenticationError(msg)
        if user.id is None:
            msg = "у пользователя должен быть id"
            raise RuntimeError(msg)
        token = self._jwt_token_service.create_access_token(user_id=user.id, login=user.login)
        return user, token
