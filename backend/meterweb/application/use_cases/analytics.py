from decimal import Decimal
from uuid import UUID

from meterweb.application.dto import AnalyticsViewDTO
from meterweb.application.ports import ReadingRepository
from meterweb.domain.metering import consumption_from_absolute_readings


class AnalyticsUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, meter_point_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        return self.execute_for_meter_point(meter_point_id, price_per_unit)

    def execute_for_meter_register(self, meter_register_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        readings = self._repository.list_for_meter_register(meter_register_id)
        consumption = _consumption(readings)
        return AnalyticsViewDTO(scope_id=meter_register_id, scope="meter_register", consumption=consumption, cost=consumption * price_per_unit)

    def execute_for_meter_point(self, meter_point_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        readings = self._repository.list_for_meter_point(meter_point_id)
        consumption = _consumption(readings)
        return AnalyticsViewDTO(scope_id=meter_point_id, scope="meter_point", consumption=consumption, cost=consumption * price_per_unit)

    def execute_for_building(self, building_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        readings = self._repository.list_for_building(building_id)
        consumption = _consumption(readings)
        return AnalyticsViewDTO(scope_id=building_id, scope="building", consumption=consumption, cost=consumption * price_per_unit)


class RecomputeAggregatesUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, meter_point_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        analytics = AnalyticsUseCase(self._repository)
        return analytics.execute_for_meter_point(meter_point_id, price_per_unit)


def _consumption(readings) -> Decimal:
    consumption = Decimal("0")
    ordered = sorted(readings, key=lambda r: (r.measured_at, r.id))
    for prev, current in zip(ordered, ordered[1:]):
        if prev.meter_register_id != current.meter_register_id:
            continue
        try:
            consumption += consumption_from_absolute_readings(prev.value, current.value)
        except ValueError:
            continue
    return consumption
