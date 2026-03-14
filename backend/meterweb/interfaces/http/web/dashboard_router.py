from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from meterweb.application.dto import BuildingCreateDTO, MeterPointCreateDTO, UnitCreateDTO
from meterweb.application.use_cases.buildings import (
    CreateBuildingUseCase,
    CreateMeterPointUseCase,
    CreateUnitUseCase,
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
)
from meterweb.interfaces.http.common import enforce_csrf, get_locale, require_auth
from meterweb.interfaces.http.templating import create_templates
from meterweb.interfaces.http.dependencies import (
    get_create_building_use_case,
    get_create_meter_point_use_case,
    get_create_unit_use_case,
    get_list_buildings_use_case,
    get_list_meter_points_use_case,
    get_list_units_use_case,
)

templates = create_templates()
router = APIRouter(tags=["web-dashboard"])


@router.get("/dashboard")
def dashboard(
    request: Request,
    list_buildings: ListBuildingsUseCase = Depends(get_list_buildings_use_case),
    list_units: ListUnitsUseCase = Depends(get_list_units_use_case),
    list_meter_points: ListMeterPointsUseCase = Depends(get_list_meter_points_use_case),
):
    require_auth(request)
    lang = get_locale(request)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "lang": lang,
            "buildings": list_buildings.execute(),
            "units": list_units.execute(),
            "meter_points": list_meter_points.execute(),
            "analytics": None,
            "reading_error": None,
            "building_error": None,
            "ocr_result": None,
        },
    )


@router.post("/dashboard/buildings", dependencies=[Depends(enforce_csrf)])
def create_building(
    request: Request,
    name: str = Form(),
    use_case: CreateBuildingUseCase = Depends(get_create_building_use_case),
    list_buildings: ListBuildingsUseCase = Depends(get_list_buildings_use_case),
    list_units: ListUnitsUseCase = Depends(get_list_units_use_case),
    list_meter_points: ListMeterPointsUseCase = Depends(get_list_meter_points_use_case),
):
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
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dashboard/units", dependencies=[Depends(enforce_csrf)])
def create_unit(request: Request, building_id: UUID = Form(), name: str = Form(), use_case: CreateUnitUseCase = Depends(get_create_unit_use_case)):
    require_auth(request)
    try:
        use_case.execute(UnitCreateDTO(building_id=building_id, name=name))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dashboard/meter-points", dependencies=[Depends(enforce_csrf)])
def create_meter_point(request: Request, unit_id: UUID = Form(), name: str = Form(), use_case: CreateMeterPointUseCase = Depends(get_create_meter_point_use_case)):
    require_auth(request)
    try:
        use_case.execute(MeterPointCreateDTO(unit_id=unit_id, name=name))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
