"""REST API: пользователи, водители, поездки."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, HTTPException, Query, status

from lib.app.common.uow import IUnitOfWork
from lib.app.domain.entities import Driver, Trip, TripStatus, User
from lib.application.dto import (
    DriverRegisterRequest,
    DriverResponse,
    TripAcceptRequest,
    TripCreateRequest,
    TripResponse,
    UserCreateRequest,
    UserResponse,
)
from lib.infra.common.errors import SaveError

router_taxi = APIRouter(tags=["такси"], route_class=DishkaRoute)


@router_taxi.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    summary="Создание пользователя",
)
async def create_user(body: UserCreateRequest, uow: FromDishka[IUnitOfWork]) -> UserResponse:
    """Регистрирует нового пользователя с уникальным логином."""
    try:
        created = await uow.users.create(
            User(None, body.login.strip(), body.first_name.strip(), body.last_name.strip()),
        )
    except SaveError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=str(exc) or "конфликт при сохранении пользователя",
        ) from exc
    return UserResponse.from_entity(created)


@router_taxi.get(
    "/users/by-login/{login}",
    summary="Поиск пользователя по логину",
)
async def get_user_by_login(login: str, uow: FromDishka[IUnitOfWork]) -> UserResponse:
    """Возвращает пользователя по логину (без учёта регистра)."""
    user = await uow.users.get_by_login(login.strip())
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="пользователь с таким логином не найден")
    return UserResponse.from_entity(user)


@router_taxi.get(
    "/users/search",
    summary="Поиск по маске имени и фамилии",
)
async def search_users_by_name(
    uow: FromDishka[IUnitOfWork],
    name_mask: Annotated[
        str,
        Query(
            ...,
            min_length=1,
            description="Шаблон LIKE для «имя фамилия»",
        ),
    ],
) -> list[UserResponse]:
    """Ищет пользователей по подстроке в конкатенации имени и фамилии."""
    users = await uow.users.search_by_name_mask(name_mask.strip())
    return [UserResponse.from_entity(u) for u in users]


@router_taxi.post(
    "/drivers",
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация водителя",
)
async def register_driver(body: DriverRegisterRequest, uow: FromDishka[IUnitOfWork]) -> DriverResponse:
    """Привязывает роль водителя к существующему пользователю."""
    user = await uow.users.get_by_id(body.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="пользователь не найден")
    try:
        driver = await uow.drivers.create(Driver(None, body.user_id))
    except SaveError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=str(exc) or "водитель уже зарегистрирован для этого пользователя",
        ) from exc
    return DriverResponse.from_entity(driver)


@router_taxi.post(
    "/trips",
    status_code=status.HTTP_201_CREATED,
    summary="Создание заказа поездки",
)
async def create_trip(body: TripCreateRequest, uow: FromDishka[IUnitOfWork]) -> TripResponse:
    """Создаёт заказ в статусе «ожидает назначения»."""
    user = await uow.users.get_by_id(body.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="пользователь не найден")
    trip = await uow.trips.create(Trip(None, body.user_id, None, TripStatus.PENDING))
    return TripResponse.from_entity(trip)


@router_taxi.get(
    "/trips/active",
    summary="Активные заказы",
)
async def list_active_trips(uow: FromDishka[IUnitOfWork]) -> list[TripResponse]:
    """Список заказов в статусах pending и active."""
    trips = await uow.trips.list_active()
    return [TripResponse.from_entity(t) for t in trips]


@router_taxi.post(
    "/trips/{trip_id}/accept",
    summary="Принятие заказа водителем",
)
async def accept_trip(
    trip_id: int,
    body: TripAcceptRequest,
    uow: FromDishka[IUnitOfWork],
) -> TripResponse:
    """Назначает водителя на заказ, переводит в active."""
    trip = await uow.trips.get_by_id(trip_id)
    if trip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="поездка не найдена")
    driver = await uow.drivers.get_by_id(body.driver_id)
    if driver is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="водитель не найден")
    updated = await uow.trips.try_accept(trip_id, body.driver_id)
    if updated is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="нельзя принять заказ: не в статусе ожидания или уже назначен",
        )
    return TripResponse.from_entity(updated)


@router_taxi.get(
    "/users/{user_id}/trips/history",
    summary="История поездок пользователя",
)
async def user_trips_history(user_id: int, uow: FromDishka[IUnitOfWork]) -> list[TripResponse]:
    """Завершённые поездки пользователя, сначала новые."""
    user = await uow.users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="пользователь не найден")
    trips = await uow.trips.list_history_for_user(user_id)
    return [TripResponse.from_entity(t) for t in trips]


@router_taxi.post(
    "/trips/{trip_id}/complete",
    summary="Завершение поездки",
)
async def complete_trip(trip_id: int, uow: FromDishka[IUnitOfWork]) -> TripResponse:
    """Переводит активную поездку в завершённую."""
    trip = await uow.trips.get_by_id(trip_id)
    if trip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="поездка не найдена")
    updated = await uow.trips.try_complete(trip_id)
    if updated is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="нельзя завершить поездку: она не активна",
        )
    return TripResponse.from_entity(updated)
