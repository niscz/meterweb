from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from meterweb.application.dto import (
    BuildingCreateDTO,
    MeterPointCreateDTO,
    ReadingCreateDTO,
    UnitCreateDTO,
)
from meterweb.application.use_cases import (
    AddReadingUseCase,
    AnalyticsUseCase,
    CreateBuildingUseCase,
    CreateMeterPointUseCase,
    CreateUnitUseCase,
    ExportUseCase,
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
    WeatherSyncUseCase,
)
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import (
    get_add_reading_use_case,
    get_analytics_use_case,
    get_create_building_use_case,
    get_create_meter_point_use_case,
    get_create_unit_use_case,
    get_export_use_case,
    get_list_buildings_use_case,
    get_list_meter_points_use_case,
    get_list_units_use_case,
    get_weather_sync_use_case,
)
from meterweb.interfaces.http.schemas import (
    AnalyticsResponse,
    BuildingCreateRequest,
    BuildingResponse,
    MeterPointCreateRequest,
    MeterPointResponse,
    ReadingCreateRequest,
    ReadingResponse,
    UnitCreateRequest,
    UnitResponse,
)

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.get("/buildings", response_model=list[BuildingResponse])
def list_buildings(request: Request, use_case: ListBuildingsUseCase = Depends(get_list_buildings_use_case)):
    require_auth(request)
    return [BuildingResponse(id=str(x.id), name=x.name) for x in use_case.execute()]


@router.post("/buildings", response_model=BuildingResponse)
def create_building(request: Request, payload: BuildingCreateRequest, use_case: CreateBuildingUseCase = Depends(get_create_building_use_case)):
    require_auth(request)
    created = use_case.execute(BuildingCreateDTO(name=payload.name))
    return BuildingResponse(id=str(created.id), name=created.name)


@router.get("/units", response_model=list[UnitResponse])
def list_units(request: Request, use_case: ListUnitsUseCase = Depends(get_list_units_use_case)):
    require_auth(request)
    return [UnitResponse(id=str(x.id), building_id=str(x.building_id), name=x.name) for x in use_case.execute()]


@router.post("/units", response_model=UnitResponse)
def create_unit(request: Request, payload: UnitCreateRequest, use_case: CreateUnitUseCase = Depends(get_create_unit_use_case)):
    require_auth(request)
    created = use_case.execute(UnitCreateDTO(building_id=payload.building_id, name=payload.name))
    return UnitResponse(id=str(created.id), building_id=str(created.building_id), name=created.name)


@router.get("/meter-points", response_model=list[MeterPointResponse])
def list_meter_points(request: Request, use_case: ListMeterPointsUseCase = Depends(get_list_meter_points_use_case)):
    require_auth(request)
    return [MeterPointResponse(id=str(x.id), unit_id=str(x.unit_id), name=x.name) for x in use_case.execute()]


@router.post("/meter-points", response_model=MeterPointResponse)
def create_meter_point(request: Request, payload: MeterPointCreateRequest, use_case: CreateMeterPointUseCase = Depends(get_create_meter_point_use_case)):
    require_auth(request)
    created = use_case.execute(MeterPointCreateDTO(unit_id=payload.unit_id, name=payload.name))
    return MeterPointResponse(id=str(created.id), unit_id=str(created.unit_id), name=created.name)


@router.post("/readings", response_model=ReadingResponse)
def add_reading(request: Request, payload: ReadingCreateRequest, use_case: AddReadingUseCase = Depends(get_add_reading_use_case)):
    require_auth(request)
    created = use_case.execute(
        ReadingCreateDTO(meter_point_id=payload.meter_point_id, measured_at=payload.measured_at, value=payload.value)
    )
    return ReadingResponse(
        id=str(created.id),
        meter_point_id=str(created.meter_point_id),
        measured_at=created.measured_at,
        value=created.value,
        plausible=created.plausible,
    )


@router.get("/analytics/{meter_point_id}", response_model=AnalyticsResponse)
def analytics(request: Request, meter_point_id: UUID, price_per_unit: Decimal = Decimal("0.35"), use_case: AnalyticsUseCase = Depends(get_analytics_use_case)):
    require_auth(request)
    data = use_case.execute(meter_point_id, price_per_unit)
    return AnalyticsResponse(meter_point_id=data.meter_point_id, consumption=data.consumption, cost=data.cost)


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


@router.get("/weather/buildings/{building_id}/station")
def get_station(request: Request, building_id: UUID, lat: float, lon: float, use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case)):
    require_auth(request)
    return {"station_id": use_case.select_station(building_id, lat, lon)}


@router.post("/weather/buildings/{building_id}/station/auto")
def set_station_auto(request: Request, building_id: UUID, use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case)):
    require_auth(request)
    use_case.set_auto_station(building_id)
    return {"status": "ok"}


@router.post("/weather/buildings/{building_id}/station/manual")
def set_station_manual(request: Request, building_id: UUID, station_id: str, use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case)):
    require_auth(request)
    use_case.set_manual_station(building_id, station_id)
    return {"status": "ok"}


@router.get("/weather/buildings/{building_id}/series")
def weather_series(
    request: Request,
    building_id: UUID,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    resolution: str = "daily",
    use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case),
):
    require_auth(request)
    points = use_case.get_series(building_id, lat, lon, start_date, end_date, resolution)
    return [{"timestamp": p.timestamp, "temperature_c": p.temperature_c, "cloud_cover_percent": p.cloud_cover_percent} for p in points]
