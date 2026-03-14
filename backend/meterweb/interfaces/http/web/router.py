from fastapi import APIRouter, status
from fastapi.templating import Jinja2Templates

from meterweb.application.dto import BuildingCreateDTO
from meterweb.application.use_cases.buildings import CreateBuildingUseCase, ListBuildingsUseCase, ListMeterPointsUseCase, ListUnitsUseCase
from meterweb.interfaces.http.common import get_locale, require_auth
from meterweb.interfaces.http.web.auth_router import router as auth_router
from meterweb.interfaces.http.web.dashboard_router import router as dashboard_router
from meterweb.interfaces.http.web.readings_router import router as readings_router
from meterweb.interfaces.http.web.reports_router import router as reports_router

router = APIRouter(tags=["web"])
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(readings_router)
router.include_router(reports_router)

templates = Jinja2Templates(directory="meterweb/templates")


def create_building(request, name: str, use_case: CreateBuildingUseCase, list_buildings: ListBuildingsUseCase, list_units: ListUnitsUseCase, list_meter_points: ListMeterPointsUseCase):
    """Backward-compatible wrapper used by unit tests."""
    require_auth(request)
    try:
        use_case.execute(BuildingCreateDTO(name=name))
    except ValueError as err:
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "lang": get_locale(request),
                "buildings": list_buildings.execute(),
                "units": list_units.execute(),
                "meter_points": list_meter_points.execute(),
                "analytics": None,
                "reading_error": None,
                "building_error": str(err),
                "ocr_result": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return None
