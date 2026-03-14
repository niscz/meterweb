from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.interfaces.http.common import get_locale, require_auth
from meterweb.interfaces.http.templating import create_templates
from meterweb.interfaces.http.dependencies import get_export_use_case

templates = create_templates()
router = APIRouter(tags=["web-reports"])


@router.get("/reports/monthly/{meter_point_id}")
def monthly_report(request: Request, meter_point_id: UUID, export_use_case: ExportUseCase = Depends(get_export_use_case)):
    require_auth(request)
    rows = export_use_case.monthly_rows(meter_point_id)
    return templates.TemplateResponse(request, "monthly_report.html", {"request": request, "rows": rows, "meter_point_id": meter_point_id, "lang": get_locale(request)})


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
    return Response(content=export_use_case.export_pdf(meter_point_id, lang=get_locale(request)), media_type="application/pdf")
