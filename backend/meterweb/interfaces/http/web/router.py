from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from meterweb.application.dto import BuildingCreateDTO, LoginDTO, MeterPointCreateDTO, ReadingCreateDTO, UnitCreateDTO
from meterweb.application.use_cases import (
    AddReadingUseCase,
    AnalyticsUseCase,
    CreateBuildingUseCase,
    CreateMeterPointUseCase,
    CreateUnitUseCase,
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
    LoginUseCase,
)
from meterweb.domain.auth import AuthenticationError
from meterweb.interfaces.http.common import TRANSLATIONS, get_locale, require_auth
from meterweb.interfaces.http.dependencies import (
    get_add_reading_use_case,
    get_analytics_use_case,
    get_create_building_use_case,
    get_create_meter_point_use_case,
    get_create_unit_use_case,
    get_list_buildings_use_case,
    get_list_meter_points_use_case,
    get_list_units_use_case,
    get_login_use_case,
)

templates = Jinja2Templates(directory="meterweb/templates")
router = APIRouter(tags=["web"])


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_page(request: Request):
    lang = get_locale(request)
    return templates.TemplateResponse(request, "login.html", {"error": None, "lang": lang})


@router.post("/login")
def login_submit(request: Request, username: str = Form(), password: str = Form(), use_case: LoginUseCase = Depends(get_login_use_case)):
    lang = get_locale(request)
    try:
        use_case.execute(LoginDTO(username=username, password=password))
    except AuthenticationError:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": TRANSLATIONS[lang]["login_error"], "lang": lang},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    request.session["username"] = username
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


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
        },
    )


@router.post("/dashboard/buildings")
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
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dashboard/units")
def create_unit(request: Request, building_id: str = Form(), name: str = Form(), use_case: CreateUnitUseCase = Depends(get_create_unit_use_case)):
    require_auth(request)
    use_case.execute(UnitCreateDTO(building_id=UUID(building_id), name=name))
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dashboard/meter-points")
def create_meter_point(request: Request, unit_id: str = Form(), name: str = Form(), use_case: CreateMeterPointUseCase = Depends(get_create_meter_point_use_case)):
    require_auth(request)
    use_case.execute(MeterPointCreateDTO(unit_id=UUID(unit_id), name=name))
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dashboard/readings")
def create_reading(
    request: Request,
    meter_point_id: str = Form(),
    measured_at: str = Form(),
    value: str = Form(),
    add_reading_use_case: AddReadingUseCase = Depends(get_add_reading_use_case),
    analytics_use_case: AnalyticsUseCase = Depends(get_analytics_use_case),
    list_buildings: ListBuildingsUseCase = Depends(get_list_buildings_use_case),
    list_units: ListUnitsUseCase = Depends(get_list_units_use_case),
    list_meter_points: ListMeterPointsUseCase = Depends(get_list_meter_points_use_case),
):
    require_auth(request)
    reading = add_reading_use_case.execute(
        ReadingCreateDTO(
            meter_point_id=UUID(meter_point_id),
            measured_at=datetime.fromisoformat(measured_at),
            value=Decimal(value),
        )
    )
    analytics = analytics_use_case.execute(UUID(meter_point_id), Decimal("0.35"))
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "lang": get_locale(request),
            "buildings": list_buildings.execute(),
            "units": list_units.execute(),
            "meter_points": list_meter_points.execute(),
            "analytics": analytics,
            "reading_error": None if reading.plausible else "Reading not plausible",
            "building_error": None,
        },
    )
