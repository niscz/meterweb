from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_export_use_case
from meterweb.interfaces.http.schemas import ReportExportRequest

router = APIRouter(tags=["v1-reports"])


@router.post("/reports/monthly")
def monthly_rows(
    request: Request,
    payload: ReportExportRequest,
    use_case: ExportUseCase = Depends(get_export_use_case),
):
    require_auth(request)
    return {"rows": use_case.monthly_rows(payload.meter_point_id)}


@router.post("/reports/export/csv")
def export_csv(
    request: Request,
    payload: ReportExportRequest,
    use_case: ExportUseCase = Depends(get_export_use_case),
):
    require_auth(request)
    return Response(content=use_case.export_csv(payload.meter_point_id), media_type="text/csv")


@router.post("/reports/export/xlsx")
def export_xlsx(
    request: Request,
    payload: ReportExportRequest,
    use_case: ExportUseCase = Depends(get_export_use_case),
):
    require_auth(request)
    return Response(content=use_case.export_xlsx(payload.meter_point_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/reports/export/pdf")
def export_pdf(
    request: Request,
    payload: ReportExportRequest,
    use_case: ExportUseCase = Depends(get_export_use_case),
):
    require_auth(request)
    return Response(content=use_case.export_pdf(payload.meter_point_id), media_type="application/pdf")
