from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.templating import Jinja2Templates

from meterweb.application.dto import PhotoReadingCreateDTO, ReadingCreateDTO
from meterweb.application.use_cases.analytics import AnalyticsUseCase
from meterweb.application.use_cases.buildings import ListBuildingsUseCase, ListMeterPointsUseCase, ListUnitsUseCase
from meterweb.application.use_cases.readings import AddPhotoReadingUseCase, AddReadingUseCase
from meterweb.bootstrap import get_container
from meterweb.interfaces.http.common import get_locale, require_auth
from meterweb.interfaces.http.dependencies import (
    get_add_photo_reading_use_case,
    get_add_reading_use_case,
    get_analytics_use_case,
    get_list_buildings_use_case,
    get_list_meter_points_use_case,
    get_list_units_use_case,
)

templates = Jinja2Templates(directory="meterweb/templates")
router = APIRouter(tags=["web-readings"])

UPLOAD_DIR = get_container().settings.uploads_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/dashboard/readings")
def create_reading(
    request: Request,
    meter_register_id: str = Form(),
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
        parsed_meter_register_id = UUID(meter_register_id)
        parsed_measured_at = datetime.fromisoformat(measured_at)
        parsed_value = Decimal(value)
        if parsed_value <= Decimal("0"):
            raise ValueError("Zählerstand muss größer als 0 sein.")

        reading = add_reading_use_case.execute(
            ReadingCreateDTO(
                meter_register_id=parsed_meter_register_id,
                measured_at=parsed_measured_at,
                value=parsed_value,
            )
        )
        analytics = None
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
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
    meter_register_id: str = Form(),
    measured_at: str = Form(),
    value: str | None = Form(default=None),
    photo: UploadFile = File(),
    add_photo_reading_use_case: AddPhotoReadingUseCase = Depends(get_add_photo_reading_use_case),
    analytics_use_case: AnalyticsUseCase = Depends(get_analytics_use_case),
):
    require_auth(request)
    parsed_meter_register_id = UUID(meter_register_id)
    parsed_measured_at = datetime.fromisoformat(measured_at)
    suffix = Path(photo.filename or "upload.jpg").suffix or ".jpg"
    file_path = UPLOAD_DIR / f"{uuid4()}{suffix}"
    file_path.write_bytes(await photo.read())
    confirmed_value = Decimal(value) if value else None
    reading, ocr_result, plausibility = add_photo_reading_use_case.execute(
        PhotoReadingCreateDTO(
            meter_register_id=parsed_meter_register_id,
            measured_at=parsed_measured_at,
            image_path=str(file_path),
        ),
        confirmed_value=confirmed_value,
    )
    analytics = None
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
