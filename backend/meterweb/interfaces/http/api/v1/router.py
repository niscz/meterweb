from fastapi import APIRouter

from meterweb.application.dto import UnitCreateDTO
from meterweb.application.use_cases.buildings import CreateUnitUseCase
from meterweb.interfaces.http.api.v1.analytics_router import router as analytics_router
from meterweb.interfaces.http.api.v1.buildings_router import router as buildings_router
from meterweb.interfaces.http.api.v1.readings_router import router as readings_router
from meterweb.interfaces.http.api.v1.weather_router import router as weather_router
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.schemas import UnitCreateRequest

router = APIRouter(prefix="/api/v1", tags=["v1"])
router.include_router(buildings_router)
router.include_router(readings_router)
router.include_router(weather_router)
router.include_router(analytics_router)


def create_unit(request, payload: UnitCreateRequest, use_case: CreateUnitUseCase):
    """Backward-compatible wrapper used by unit tests."""
    require_auth(request)
    return use_case.execute(UnitCreateDTO(building_id=payload.building_id, name=payload.name))
