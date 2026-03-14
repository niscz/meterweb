from decimal import Decimal
from uuid import UUID

from meterweb.application.dto import AnalyticsViewDTO
from meterweb.application.ports import ReadingRepository
from meterweb.domain.metering import consumption_from_absolute_readings


class AnalyticsUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, meter_point_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        readings = self._repository.list_for_meter_point(meter_point_id)
        consumption = Decimal("0")
        for prev, current in zip(readings, readings[1:]):
            try:
                consumption += consumption_from_absolute_readings(
                    prev.value,
                    current.value,
                )
            except ValueError:
                continue
        return AnalyticsViewDTO(
            meter_point_id=meter_point_id,
            consumption=consumption,
            cost=consumption * price_per_unit,
        )


class RecomputeAggregatesUseCase:
    def __init__(self, repository: ReadingRepository) -> None:
        self._repository = repository

    def execute(self, meter_point_id: UUID, price_per_unit: Decimal) -> AnalyticsViewDTO:
        analytics = AnalyticsUseCase(self._repository)
        return analytics.execute(meter_point_id, price_per_unit)
