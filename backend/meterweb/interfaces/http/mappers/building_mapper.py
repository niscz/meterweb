from meterweb.application.dto import BuildingViewDTO, MeterPointViewDTO, UnitViewDTO
from meterweb.interfaces.http.schemas import BuildingResponse, MeterPointResponse, UnitResponse


def to_building_response(dto: BuildingViewDTO) -> BuildingResponse:
    return BuildingResponse(id=str(dto.id), name=dto.name)


def to_unit_response(dto: UnitViewDTO) -> UnitResponse:
    return UnitResponse(id=str(dto.id), building_id=str(dto.building_id), name=dto.name)


def to_meter_point_response(dto: MeterPointViewDTO) -> MeterPointResponse:
    return MeterPointResponse(id=str(dto.id), unit_id=str(dto.unit_id), name=dto.name)
