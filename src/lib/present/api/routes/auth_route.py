"""REST API: регистрация и вход."""

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, HTTPException, status

from lib.application.auth.auth_service import AuthService
from lib.application.auth.errors import AuthenticationError
from lib.application.dto import AuthLoginRequest, AuthRegisterRequest, AuthTokenResponse
from lib.infra.common.errors import SaveError

router_auth = APIRouter(tags=["аутентификация"], route_class=DishkaRoute)


@router_auth.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
)
async def register(body: AuthRegisterRequest, auth_service: FromDishka[AuthService]) -> AuthTokenResponse:
    """Создаёт учётную запись с паролем и возвращает JWT."""
    try:
        user, token = await auth_service.register(
            login=body.login,
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
        )
    except SaveError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=str(exc) or "конфликт при регистрации пользователя",
        ) from exc
    return AuthTokenResponse.from_user_and_token(user, token)


@router_auth.post(
    "/auth/login",
    summary="Вход пользователя",
)
async def login(body: AuthLoginRequest, auth_service: FromDishka[AuthService]) -> AuthTokenResponse:
    """Проверяет логин и пароль, возвращает JWT."""
    try:
        user, token = await auth_service.login(login=body.login, password=body.password)
    except AuthenticationError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return AuthTokenResponse.from_user_and_token(user, token)
