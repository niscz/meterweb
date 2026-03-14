from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_export_use_case

templates = Jinja2Templates(directory="meterweb/templates")
router = APIRouter(tags=["web-reports"])


@router.get("/reports/monthly/{meter_point_id}")
def monthly_report(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    rows = export_use_case.monthly_rows(meter_point_id)
    return templates.TemplateResponse(request, "monthly_report.html", {"request": request, "rows": rows, "meter_point_id": meter_point_id})


@router.get("/exports/csv/{meter_point_id}")
def export_csv(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=export_use_case.export_csv(meter_point_id), media_type="text/csv")


@router.get("/exports/xlsx/{meter_point_id}")
def export_xlsx(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=export_use_case.export_xlsx(meter_point_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/exports/pdf/{meter_point_id}")
def export_pdf(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    return Response(content=export_use_case.export_pdf(meter_point_id), media_type="application/pdf")
