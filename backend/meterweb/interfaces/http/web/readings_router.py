from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from meterweb.application.dto import PhotoReadingCreateDTO, ReadingCreateDTO
from meterweb.application.use_cases.analytics import AnalyticsUseCase
from meterweb.application.use_cases.buildings import ListBuildingsUseCase, ListMeterPointsUseCase, ListUnitsUseCase
from meterweb.application.use_cases.readings import AddPhotoReadingUseCase, AddReadingUseCase
from meterweb.bootstrap import get_container
from meterweb.infrastructure.db import get_session
from meterweb.infrastructure.repositories import SqlAlchemyReadingRepository
from meterweb.interfaces.http.common import enforce_csrf, get_locale, require_auth, translate
from meterweb.interfaces.http.templating import create_templates
from meterweb.interfaces.http.dependencies import (
    get_add_photo_reading_use_case,
    get_add_reading_use_case,
    get_analytics_use_case,
    get_list_buildings_use_case,
    get_list_meter_points_use_case,
    get_list_units_use_case,
)

templates = create_templates()
router = APIRouter(tags=["web-readings"])


UPLOAD_DIR = get_container().settings.uploads_dir
PHOTO_UPLOAD_MAX_SIZE_BYTES = get_container().settings.photo_upload_max_size_bytes
ALLOWED_PHOTO_MIME_TYPES = frozenset(get_container().settings.photo_upload_allowed_mime_types)
ALLOWED_PHOTO_EXTENSIONS = frozenset(get_container().settings.photo_upload_allowed_extensions)
PHOTO_UPLOAD_CHUNK_SIZE = 1024 * 1024


def _cleanup_upload(file_path: Path | None) -> None:
    if file_path and file_path.exists():
        file_path.unlink(missing_ok=True)


async def _save_upload_streaming(photo: UploadFile) -> Path:
    suffix = Path(photo.filename or "upload.jpg").suffix.lower() or ".jpg"
    content_type = (photo.content_type or "").lower()

    if suffix not in ALLOWED_PHOTO_EXTENSIONS or content_type not in ALLOWED_PHOTO_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiger Dateityp.")

    file_path = UPLOAD_DIR / f"{uuid4()}{suffix}"
    total_written = 0

    try:
        with file_path.open("wb") as target:
            while True:
                chunk = await photo.read(PHOTO_UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > PHOTO_UPLOAD_MAX_SIZE_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Datei ist zu groß.")
                target.write(chunk)
    except Exception:
        _cleanup_upload(file_path)
        raise
    finally:
        await photo.close()

    return file_path


def _dashboard_response(
    request: Request,
    *,
    analytics_use_case: AnalyticsUseCase,
    list_buildings: ListBuildingsUseCase,
    list_units: ListUnitsUseCase,
    list_meter_points: ListMeterPointsUseCase,
    meter_point_id: UUID | None,
    reading_error: str | None,
):
    analytics = analytics_use_case.execute(meter_point_id, Decimal("0.35")) if meter_point_id else None
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "lang": get_locale(request),
            "buildings": list_buildings.execute(),
            "units": list_units.execute(),
            "meter_points": list_meter_points.execute(),
            "analytics": analytics,
            "reading_error": reading_error,
            "building_error": None,
            "ocr_result": None,
        },
    )


def _as_uuid(value: UUID | str) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(value)


def _resolve_register_id(session: Session, meter_register_id: UUID | str | None, meter_point_id: UUID | str | None) -> UUID:
    if meter_register_id:
        return _as_uuid(meter_register_id)
    if not meter_point_id:
        raise ValueError("Bitte Messpunkt oder Zählwerk angeben.")
    register_id = SqlAlchemyReadingRepository(session).get_current_register_for_meter_point(_as_uuid(meter_point_id))
    if register_id is None:
        raise ValueError("Messpunkt hat kein aktives Register.")
    return register_id


@router.post("/dashboard/readings", dependencies=[Depends(enforce_csrf)])
def create_reading(
    request: Request,
    meter_register_id: UUID | None = Form(default=None),
    meter_point_id: UUID | None = Form(default=None),
    measured_at: str = Form(),
    value: str = Form(),
    add_reading_use_case: AddReadingUseCase = Depends(get_add_reading_use_case),
    analytics_use_case: AnalyticsUseCase = Depends(get_analytics_use_case),
    list_buildings: ListBuildingsUseCase = Depends(get_list_buildings_use_case),
    list_units: ListUnitsUseCase = Depends(get_list_units_use_case),
    list_meter_points: ListMeterPointsUseCase = Depends(get_list_meter_points_use_case),
    session: Session = Depends(get_session),
):
    require_auth(request)
    try:
        parsed_meter_register_id = _resolve_register_id(session, meter_register_id, meter_point_id)
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
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return _dashboard_response(
        request,
        analytics_use_case=analytics_use_case,
        list_buildings=list_buildings,
        list_units=list_units,
        list_meter_points=list_meter_points,
        meter_point_id=meter_point_id,
        reading_error=None if reading.plausible else translate(get_locale(request), "reading_not_plausible"),
    )


@router.post("/dashboard/readings/photo", dependencies=[Depends(enforce_csrf)])
async def create_photo_reading(
    request: Request,
    meter_register_id: UUID | None = Form(default=None),
    meter_point_id: UUID | None = Form(default=None),
    measured_at: str = Form(),
    value: str | None = Form(default=None),
    photo: UploadFile = File(),
    add_photo_reading_use_case: AddPhotoReadingUseCase = Depends(get_add_photo_reading_use_case),
    analytics_use_case: AnalyticsUseCase = Depends(get_analytics_use_case),
    list_buildings: ListBuildingsUseCase = Depends(get_list_buildings_use_case),
    list_units: ListUnitsUseCase = Depends(get_list_units_use_case),
    list_meter_points: ListMeterPointsUseCase = Depends(get_list_meter_points_use_case),
    session: Session = Depends(get_session),
):
    require_auth(request)
    file_path: Path | None = None
    try:
        parsed_meter_register_id = _resolve_register_id(session, meter_register_id, meter_point_id)
        parsed_measured_at = datetime.fromisoformat(measured_at)
        confirmed_value = Decimal(value) if value else None

        file_path = await _save_upload_streaming(photo)

        reading, ocr_result, plausibility = add_photo_reading_use_case.execute(
            PhotoReadingCreateDTO(
                meter_register_id=parsed_meter_register_id,
                measured_at=parsed_measured_at,
                image_path=str(file_path),
            ),
            confirmed_value=confirmed_value,
        )
    except HTTPException:
        _cleanup_upload(file_path)
        raise
    except (ValueError, InvalidOperation):
        _cleanup_upload(file_path)
        return _dashboard_response(
            request,
            analytics_use_case=analytics_use_case,
            list_buildings=list_buildings,
            list_units=list_units,
            list_meter_points=list_meter_points,
            meter_point_id=meter_point_id,
            reading_error=translate(get_locale(request), "photo_reading_invalid_input"),
        )
    except (RuntimeError, FileNotFoundError):
        _cleanup_upload(file_path)
        return _dashboard_response(
            request,
            analytics_use_case=analytics_use_case,
            list_buildings=list_buildings,
            list_units=list_units,
            list_meter_points=list_meter_points,
            meter_point_id=meter_point_id,
            reading_error=translate(get_locale(request), "photo_reading_ocr_failed"),
        )
    except Exception:
        _cleanup_upload(file_path)
        return _dashboard_response(
            request,
            analytics_use_case=analytics_use_case,
            list_buildings=list_buildings,
            list_units=list_units,
            list_meter_points=list_meter_points,
            meter_point_id=meter_point_id,
            reading_error=translate(get_locale(request), "photo_reading_failed"),
        )

    analytics = analytics_use_case.execute(meter_point_id, Decimal("0.35")) if meter_point_id else None
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
