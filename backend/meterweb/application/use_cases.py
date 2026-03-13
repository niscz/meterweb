from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from meterweb.application.dto import (
    AnalyticsViewDTO,
    BuildingCreateDTO,
    BuildingViewDTO,
    LoginDTO,
    MeterPointCreateDTO,
    MeterPointViewDTO,
    ReadingCreateDTO,
    ReadingViewDTO,
    UnitCreateDTO,
    UnitViewDTO,
)
from meterweb.application.ports import (
    Authenticator,
    BuildingRepository,
    MeterPointRepository,
    ReadingRepository,
    UnitRepository,
)
from meterweb.domain.auth import Credentials, User
from meterweb.domain.building import Building, BuildingDomainService, BuildingName
from meterweb.domain.metering import MeterPoint, Unit, consumption_from_absolute_readings


class LoginUseCase:
    def __init__(self, authenticator: Authenticator) -> None:
        self._authenticator = authenticator

    def execute(self, data: LoginDTO) -> User:
        return self._authenticator.authenticate(
            Credentials(username=data.username, password=data.password)
        )


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
        return [UnitViewDTO(id=i.id, building_id=i.building_id, name=i.name) for i in self._repository.list_all()]


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
        return [MeterPointViewDTO(id=i.id, unit_id=i.unit_id, name=i.name) for i in self._repository.list_all()]


class AddReadingUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, data: ReadingCreateDTO) -> ReadingViewDTO:
        measured_at = data.measured_at
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)
        created = self._repository.add_manual(data.meter_point_id, measured_at, data.value)
        readings = self._repository.list_for_meter_point(data.meter_point_id)
        plausible = True
        if len(readings) >= 2:
            previous = readings[-2].value
            try:
                _ = consumption_from_absolute_readings(previous, readings[-1].value)
            except ValueError:
                plausible = False
        return ReadingViewDTO(
            id=created.id,
            meter_point_id=data.meter_point_id,
            measured_at=created.measured_at,
            value=created.value,
            plausible=plausible,
        )


class AnalyticsUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, meter_point_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        readings = self._repository.list_for_meter_point(meter_point_id)
        consumption = Decimal("0")
        for prev, current in zip(readings, readings[1:]):
            consumption += consumption_from_absolute_readings(prev.value, current.value)
        return AnalyticsViewDTO(
            meter_point_id=meter_point_id,
            consumption=consumption,
            cost=consumption * price_per_unit,
        )
