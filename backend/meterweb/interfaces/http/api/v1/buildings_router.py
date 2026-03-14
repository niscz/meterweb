from fastapi import APIRouter, Depends, Request

from meterweb.application.dto import BuildingCreateDTO, MeterPointCreateDTO, UnitCreateDTO
from meterweb.application.use_cases.buildings import (
    CreateBuildingUseCase,
    CreateMeterPointWithDefaultDeviceUseCase,
    CreateUnitUseCase,
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
)
from meterweb.interfaces.http.common import enforce_csrf, require_auth
from meterweb.interfaces.http.dependencies import (
    get_create_building_use_case,
    get_create_meter_point_use_case,
    get_create_unit_use_case,
    get_list_buildings_use_case,
    get_list_meter_points_use_case,
    get_list_units_use_case,
)
from meterweb.interfaces.http.mappers import to_building_response, to_meter_point_response, to_unit_response
from meterweb.interfaces.http.schemas import (
    BuildingCreateRequest,
    BuildingResponse,
    MeterPointCreateRequest,
    MeterPointResponse,
    UnitCreateRequest,
    UnitResponse,
)

router = APIRouter(tags=["v1-buildings"])


@router.get("/buildings", response_model=list[BuildingResponse])
def list_buildings(request: Request, use_case: ListBuildingsUseCase = Depends(get_list_buildings_use_case)):
    require_auth(request)
    return [to_building_response(item) for item in use_case.execute()]


@router.post("/buildings", response_model=BuildingResponse, dependencies=[Depends(enforce_csrf)])
def create_building(request: Request, payload: BuildingCreateRequest, use_case: CreateBuildingUseCase = Depends(get_create_building_use_case)):
    require_auth(request)
    return to_building_response(use_case.execute(BuildingCreateDTO(name=payload.name)))


@router.get("/units", response_model=list[UnitResponse])
def list_units(request: Request, use_case: ListUnitsUseCase = Depends(get_list_units_use_case)):
    require_auth(request)
    return [to_unit_response(item) for item in use_case.execute()]


@router.post("/units", response_model=UnitResponse, dependencies=[Depends(enforce_csrf)])
def create_unit(request: Request, payload: UnitCreateRequest, use_case: CreateUnitUseCase = Depends(get_create_unit_use_case)):
    require_auth(request)
    return to_unit_response(use_case.execute(UnitCreateDTO(building_id=payload.building_id, name=payload.name)))


@router.get("/meter-points", response_model=list[MeterPointResponse])
def list_meter_points(request: Request, use_case: ListMeterPointsUseCase = Depends(get_list_meter_points_use_case)):
    require_auth(request)
    return [to_meter_point_response(item) for item in use_case.execute()]


@router.post("/meter-points", response_model=MeterPointResponse, dependencies=[Depends(enforce_csrf)])
def create_meter_point(request: Request, payload: MeterPointCreateRequest, use_case: CreateMeterPointWithDefaultDeviceUseCase = Depends(get_create_meter_point_use_case)):
    require_auth(request)
    return to_meter_point_response(use_case.execute(MeterPointCreateDTO(unit_id=payload.unit_id, name=payload.name)))
