from uuid import uuid4

from meterweb.application.dto import (
    BuildingCreateDTO,
    BuildingViewDTO,
    MeterPointCreateDTO,
    MeterPointViewDTO,
    UnitCreateDTO,
    UnitViewDTO,
)
from meterweb.application.ports import (
    BuildingRepository,
    MeterPointRepository,
    UnitRepository,
)
from meterweb.domain.building import Building, BuildingDomainService, BuildingName
from meterweb.domain.metering import MeterPoint, Unit


class CreateBuildingUseCase:
    def __init__(self, repository: BuildingRepository) -> None:
        self._repository = repository

    def execute(self, data: BuildingCreateDTO) -> BuildingViewDTO:
        all_buildings = self._repository.list_all()
        names = {item.name.value.lower() for item in all_buildings}
        candidate_name = BuildingName(data.name)
        BuildingDomainService.ensure_name_is_unique(candidate_name, names)

        building = Building.create(candidate_name.value)
        self._repository.add(building)
        return BuildingViewDTO(id=building.id, name=building.name.value)


class ListBuildingsUseCase:
    def __init__(self, repository: BuildingRepository) -> None:
        self._repository = repository

    def execute(self) -> list[BuildingViewDTO]:
        return [
            BuildingViewDTO(id=item.id, name=item.name.value)
            for item in self._repository.list_all()
        ]


class CreateUnitUseCase:
    def __init__(self, repository: UnitRepository) -> None:
        self._repository = repository

    def execute(self, data: UnitCreateDTO) -> UnitViewDTO:
        unit = Unit(id=uuid4(), building_id=data.building_id, name=data.name.strip())
        if not unit.name:
            raise ValueError("Einheitsname darf nicht leer sein.")
        self._repository.add(unit)
        return UnitViewDTO(id=unit.id, building_id=unit.building_id, name=unit.name)


class ListUnitsUseCase:
    def __init__(self, repository: UnitRepository) -> None:
        self._repository = repository

    def execute(self) -> list[UnitViewDTO]:
        return [
            UnitViewDTO(id=i.id, building_id=i.building_id, name=i.name)
            for i in self._repository.list_all()
        ]


class CreateMeterPointUseCase:
    def __init__(self, repository: MeterPointRepository) -> None:
        self._repository = repository

    def execute(self, data: MeterPointCreateDTO) -> MeterPointViewDTO:
        mp = MeterPoint(id=uuid4(), unit_id=data.unit_id, name=data.name.strip())
        if not mp.name:
            raise ValueError("Messpunktname darf nicht leer sein.")
        self._repository.add(mp)
        return MeterPointViewDTO(id=mp.id, unit_id=mp.unit_id, name=mp.name)


class ListMeterPointsUseCase:
    def __init__(self, repository: MeterPointRepository) -> None:
        self._repository = repository

    def execute(self) -> list[MeterPointViewDTO]:
        return [
            MeterPointViewDTO(id=i.id, unit_id=i.unit_id, name=i.name)
            for i in self._repository.list_all()
        ]
