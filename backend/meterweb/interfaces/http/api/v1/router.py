from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

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
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
)
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import (
    get_add_reading_use_case,
    get_analytics_use_case,
    get_create_building_use_case,
    get_create_meter_point_use_case,
    get_create_unit_use_case,
    get_list_buildings_use_case,
    get_list_meter_points_use_case,
    get_list_units_use_case,
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
    try:
        created = use_case.execute(BuildingCreateDTO(name=payload.name))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return BuildingResponse(id=str(created.id), name=created.name)


@router.get("/units", response_model=list[UnitResponse])
def list_units(request: Request, use_case: ListUnitsUseCase = Depends(get_list_units_use_case)):
    require_auth(request)
    return [UnitResponse(id=str(x.id), building_id=str(x.building_id), name=x.name) for x in use_case.execute()]


@router.post("/units", response_model=UnitResponse)
def create_unit(request: Request, payload: UnitCreateRequest, use_case: CreateUnitUseCase = Depends(get_create_unit_use_case)):
    require_auth(request)
    created = use_case.execute(UnitCreateDTO(building_id=UUID(payload.building_id), name=payload.name))
    return UnitResponse(id=str(created.id), building_id=str(created.building_id), name=created.name)


@router.get("/meter-points", response_model=list[MeterPointResponse])
def list_meter_points(request: Request, use_case: ListMeterPointsUseCase = Depends(get_list_meter_points_use_case)):
    require_auth(request)
    return [MeterPointResponse(id=str(x.id), unit_id=str(x.unit_id), name=x.name) for x in use_case.execute()]


@router.post("/meter-points", response_model=MeterPointResponse)
def create_meter_point(request: Request, payload: MeterPointCreateRequest, use_case: CreateMeterPointUseCase = Depends(get_create_meter_point_use_case)):
    require_auth(request)
    created = use_case.execute(MeterPointCreateDTO(unit_id=UUID(payload.unit_id), name=payload.name))
    return MeterPointResponse(id=str(created.id), unit_id=str(created.unit_id), name=created.name)


@router.post("/readings", response_model=ReadingResponse)
def add_reading(request: Request, payload: ReadingCreateRequest, use_case: AddReadingUseCase = Depends(get_add_reading_use_case)):
    require_auth(request)
    created = use_case.execute(
        ReadingCreateDTO(meter_point_id=UUID(payload.meter_point_id), measured_at=payload.measured_at, value=payload.value)
    )
    return ReadingResponse(
        id=str(created.id),
        meter_point_id=str(created.meter_point_id),
        measured_at=created.measured_at,
        value=created.value,
        plausible=created.plausible,
    )


@router.get("/analytics/{meter_point_id}", response_model=AnalyticsResponse)
def analytics(request: Request, meter_point_id: str, price_per_unit: Decimal = Decimal("0.35"), use_case: AnalyticsUseCase = Depends(get_analytics_use_case)):
    require_auth(request)
    data = use_case.execute(UUID(meter_point_id), price_per_unit)
    return AnalyticsResponse(meter_point_id=str(data.meter_point_id), consumption=data.consumption, cost=data.cost)
