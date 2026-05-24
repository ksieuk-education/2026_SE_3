"""Проверка доступности сервиса."""

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from lib.application.dto import HealthResponse
from lib.main.settings import Settings

router_health = APIRouter(tags=["health"], route_class=DishkaRoute)


@router_health.get(
    "/health",
    summary="Health check",
)
async def health(settings: FromDishka[Settings]) -> HealthResponse:
    """Возвращает статус сервиса и сведения о приложении из настроек."""
    return HealthResponse(
        status="healthy",
        title=settings.app_settings.title,
        version=settings.app_settings.version,
    )
