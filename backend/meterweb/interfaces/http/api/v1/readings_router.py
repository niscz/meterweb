from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from meterweb.application.dto import ReadingCreateDTO
from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.application.use_cases.readings import AddReadingUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_add_reading_use_case, get_export_use_case
from meterweb.interfaces.http.mappers import to_reading_response
from meterweb.interfaces.http.schemas import ReadingCreateRequest, ReadingResponse

router = APIRouter(tags=["v1-readings"])


@router.post("/readings", response_model=ReadingResponse)
def add_reading(request: Request, payload: ReadingCreateRequest, use_case: AddReadingUseCase = Depends(get_add_reading_use_case)):
    require_auth(request)
    created = use_case.execute(
        ReadingCreateDTO(meter_point_id=payload.meter_point_id, measured_at=payload.measured_at, value=payload.value)
    )
    return to_reading_response(created)


@router.post("/export/csv")
def export_csv(request: Request, meter_point_id: UUID, use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=use_case.export_csv(meter_point_id), media_type="text/csv")


@router.post("/export/xlsx")
def export_xlsx(request: Request, meter_point_id: UUID, use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=use_case.export_xlsx(meter_point_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/export/pdf")
def export_pdf(request: Request, meter_point_id: UUID, use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=use_case.export_pdf(meter_point_id), media_type="application/pdf")
