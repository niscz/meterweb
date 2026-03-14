from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.interfaces.http.common import enforce_csrf, get_locale, require_auth
from meterweb.interfaces.http.dependencies import get_export_use_case
from meterweb.interfaces.http.schemas import ReportExportRequest

router = APIRouter(tags=["v1-reports"])


@router.post("/reports/monthly", dependencies=[Depends(enforce_csrf)])
def monthly_rows(
    request: Request,
    payload: ReportExportRequest,
    use_case: ExportUseCase = Depends(get_export_use_case),
):
    require_auth(request)
    if payload.meter_register_id:
        return {"rows": use_case.monthly_rows_for_meter_register(payload.meter_register_id)}
    if payload.meter_point_id:
        return {"rows": use_case.monthly_rows_for_meter_point(payload.meter_point_id)}
    if payload.building_id:
        return {"rows": use_case.monthly_rows_for_building(payload.building_id)}
    raise HTTPException(status_code=422, detail="scope required")


@router.post("/reports/export/csv", dependencies=[Depends(enforce_csrf)])
def export_csv(
    request: Request,
    payload: ReportExportRequest,
    use_case: ExportUseCase = Depends(get_export_use_case),
):
    require_auth(request)
    if payload.meter_register_id:
        return Response(content=use_case.export_csv_for_meter_register(payload.meter_register_id), media_type="text/csv")
    if payload.meter_point_id:
        return Response(content=use_case.export_csv(payload.meter_point_id), media_type="text/csv")
    if payload.building_id:
        return Response(content=use_case.export_csv_for_building(payload.building_id), media_type="text/csv")
    raise HTTPException(status_code=422, detail="scope required")


@router.post("/reports/export/xlsx", dependencies=[Depends(enforce_csrf)])
def export_xlsx(
    request: Request,
    payload: ReportExportRequest,
    use_case: ExportUseCase = Depends(get_export_use_case),
):
    require_auth(request)
    if payload.meter_register_id:
        return Response(content=use_case.export_xlsx_for_meter_register(payload.meter_register_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if payload.meter_point_id:
        return Response(content=use_case.export_xlsx(payload.meter_point_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if payload.building_id:
        return Response(content=use_case.export_xlsx_for_building(payload.building_id), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    raise HTTPException(status_code=422, detail="scope required")


@router.post("/reports/export/pdf", dependencies=[Depends(enforce_csrf)])
def export_pdf(
    request: Request,
    payload: ReportExportRequest,
    use_case: ExportUseCase = Depends(get_export_use_case),
):
    require_auth(request)
    if payload.meter_register_id:
        return Response(content=use_case.export_pdf_for_meter_register(payload.meter_register_id, lang=get_locale(request)), media_type="application/pdf")
    if payload.meter_point_id:
        return Response(content=use_case.export_pdf(payload.meter_point_id, lang=get_locale(request)), media_type="application/pdf")
    if payload.building_id:
        return Response(content=use_case.export_pdf_for_building(payload.building_id, lang=get_locale(request)), media_type="application/pdf")
    raise HTTPException(status_code=422, detail="scope required")
