from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from meterweb.application.dto import OCRDecisionDTO, ReadingCreateDTO
from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.application.use_cases.readings import AddReadingUseCase, ConfirmReadingUseCase, CorrectReadingUseCase
from meterweb.infrastructure.db import get_session
from meterweb.infrastructure.repositories import SqlAlchemyReadingRepository
from meterweb.interfaces.http.common import enforce_csrf, require_auth
from meterweb.interfaces.http.dependencies import (
    get_add_reading_use_case,
    get_confirm_reading_use_case,
    get_correct_reading_use_case,
    get_export_use_case,
)
from meterweb.interfaces.http.mappers import to_reading_response
from meterweb.interfaces.http.schemas import ReadingCorrectRequest, ReadingCreateRequest, ReadingResponse

router = APIRouter(tags=["v1-readings"])


@router.post("/readings", response_model=ReadingResponse, dependencies=[Depends(enforce_csrf)])
def add_reading(request: Request, payload: ReadingCreateRequest, use_case: AddReadingUseCase = Depends(get_add_reading_use_case)):
    require_auth(request)
    created = use_case.execute(
        ReadingCreateDTO(meter_register_id=payload.meter_register_id, measured_at=payload.measured_at, value=payload.value)
    )
    return to_reading_response(created)


@router.get("/meter-points/{meter_point_id}/current-register")
def current_register_for_meter_point(request: Request, meter_point_id: UUID, session: Session = Depends(get_session)):
    require_auth(request)
    register_id = SqlAlchemyReadingRepository(session).get_current_register_for_meter_point(meter_point_id)
    if register_id is None:
        raise HTTPException(status_code=404, detail="Messpunkt hat kein aktives Register.")
    return {"meter_register_id": str(register_id)}


@router.post("/export/csv", dependencies=[Depends(enforce_csrf)])
def export_csv(request: Request, meter_point_id: UUID, use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=use_case.export_csv(meter_point_id), media_type="text/csv")


@router.post("/export/xlsx", dependencies=[Depends(enforce_csrf)])
def export_xlsx(request: Request, meter_point_id: UUID, use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=use_case.export_xlsx(meter_point_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/export/pdf", dependencies=[Depends(enforce_csrf)])
def export_pdf(request: Request, meter_point_id: UUID, use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=use_case.export_pdf(meter_point_id), media_type="application/pdf")


@router.post("/readings/{reading_id}/confirm", response_model=ReadingResponse, dependencies=[Depends(enforce_csrf)])
def confirm_reading(
    request: Request,
    reading_id: UUID,
    use_case: ConfirmReadingUseCase = Depends(get_confirm_reading_use_case),
):
    require_auth(request)
    updated = use_case.execute(OCRDecisionDTO(reading_id=reading_id))
    return to_reading_response(updated)


@router.post("/readings/{reading_id}/correct", response_model=ReadingResponse, dependencies=[Depends(enforce_csrf)])
def correct_reading(
    request: Request,
    reading_id: UUID,
    payload: ReadingCorrectRequest,
    use_case: CorrectReadingUseCase = Depends(get_correct_reading_use_case),
):
    require_auth(request)
    updated = use_case.execute(OCRDecisionDTO(reading_id=reading_id, value=payload.value))
    return to_reading_response(updated)
