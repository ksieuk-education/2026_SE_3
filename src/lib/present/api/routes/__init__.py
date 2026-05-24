"""HTTP-роуты."""

from lib.present.api.routes.auth_route import router_auth
from lib.present.api.routes.health_route import router_health
from lib.present.api.routes.taxi_route import router_taxi

__all__ = ["router_auth", "router_health", "router_taxi"]
