from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from meterweb.application.dto import BuildingCreateDTO, LoginDTO, MeterPointCreateDTO, PhotoReadingCreateDTO, ReadingCreateDTO, UnitCreateDTO
from meterweb.application.use_cases import (
    AddPhotoReadingUseCase,
    AddReadingUseCase,
    AnalyticsUseCase,
    CreateBuildingUseCase,
    CreateMeterPointUseCase,
    CreateUnitUseCase,
    ExportUseCase,
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
    LoginUseCase,
)
from meterweb.domain.auth import AuthenticationError
from meterweb.interfaces.http.common import TRANSLATIONS, get_locale, require_auth
from meterweb.interfaces.http.dependencies import (
    get_add_photo_reading_use_case,
    get_add_reading_use_case,
    get_analytics_use_case,
    get_create_building_use_case,
    get_create_meter_point_use_case,
    get_create_unit_use_case,
    get_export_use_case,
    get_list_buildings_use_case,
    get_list_meter_points_use_case,
    get_list_units_use_case,
    get_login_use_case,
)

templates = Jinja2Templates(directory="meterweb/templates")
router = APIRouter(tags=["web"])

UPLOAD_DIR = Path("/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
            "ocr_result": None,
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
                "ocr_result": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dashboard/units")
def create_unit(request: Request, building_id: str = Form(), name: str = Form(), use_case: CreateUnitUseCase = Depends(get_create_unit_use_case)):
    require_auth(request)
    try:
        parsed_building_id = UUID(building_id)
        use_case.execute(UnitCreateDTO(building_id=parsed_building_id, name=name))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dashboard/meter-points")
def create_meter_point(request: Request, unit_id: str = Form(), name: str = Form(), use_case: CreateMeterPointUseCase = Depends(get_create_meter_point_use_case)):
    require_auth(request)
    try:
        parsed_unit_id = UUID(unit_id)
        use_case.execute(MeterPointCreateDTO(unit_id=parsed_unit_id, name=name))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
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
    try:
        parsed_meter_point_id = UUID(meter_point_id)
        parsed_measured_at = datetime.fromisoformat(measured_at)
        parsed_value = Decimal(value)
        if parsed_value <= Decimal("0"):
            raise ValueError("Zählerstand muss größer als 0 sein.")

        reading = add_reading_use_case.execute(
            ReadingCreateDTO(
                meter_point_id=parsed_meter_point_id,
                measured_at=parsed_measured_at,
                value=parsed_value,
            )
        )
        analytics = analytics_use_case.execute(parsed_meter_point_id, Decimal("0.35"))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
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
            "ocr_result": None,
        },
    )


@router.post("/dashboard/readings/photo")
async def create_photo_reading(
    request: Request,
    meter_point_id: str = Form(),
    measured_at: str = Form(),
    value: str | None = Form(default=None),
    photo: UploadFile = File(),
    add_photo_reading_use_case: AddPhotoReadingUseCase = Depends(get_add_photo_reading_use_case),
    analytics_use_case: AnalyticsUseCase = Depends(get_analytics_use_case),
):
    require_auth(request)
    parsed_meter_point_id = UUID(meter_point_id)
    parsed_measured_at = datetime.fromisoformat(measured_at)
    suffix = Path(photo.filename or "upload.jpg").suffix or ".jpg"
    file_path = UPLOAD_DIR / f"{uuid4()}{suffix}"
    file_path.write_bytes(await photo.read())
    confirmed_value = Decimal(value) if value else None
    reading, ocr_result, plausibility = add_photo_reading_use_case.execute(
        PhotoReadingCreateDTO(
            meter_point_id=parsed_meter_point_id,
            measured_at=parsed_measured_at,
            image_path=str(file_path),
        ),
        confirmed_value=confirmed_value,
    )
    analytics = analytics_use_case.execute(parsed_meter_point_id, Decimal("0.35"))
    return templates.TemplateResponse(
        request,
        "capture_confirm.html",
        {
            "lang": get_locale(request),
            "reading": reading,
            "ocr_result": ocr_result,
            "plausibility_warning": plausibility.warning,
            "analytics": analytics,
            "image_path": str(file_path),
        },
    )


@router.get("/reports/monthly/{meter_point_id}")
def monthly_report(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    rows = export_use_case.monthly_rows(meter_point_id)
    return templates.TemplateResponse(request, "monthly_report.html", {"request": request, "rows": rows, "meter_point_id": meter_point_id})


@router.get("/exports/csv/{meter_point_id}")
def export_csv(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    from fastapi.responses import Response

    return Response(content=export_use_case.export_csv(meter_point_id), media_type="text/csv")


@router.get("/exports/xlsx/{meter_point_id}")
def export_xlsx(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    from fastapi.responses import Response

    return Response(content=export_use_case.export_xlsx(meter_point_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/exports/pdf/{meter_point_id}")
def export_pdf(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    from fastapi.responses import Response

    return Response(content=export_use_case.export_pdf(meter_point_id), media_type="application/pdf")
