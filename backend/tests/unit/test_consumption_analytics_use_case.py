from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from meterweb.application.use_cases import AnalyticsUseCase
from meterweb.domain.metering import Reading


class FakeReadingRepository:
    def __init__(self, readings: list[Reading]):
        self._readings = readings

    def list_for_meter_register(self, meter_register_id):
        return [r for r in self._readings if r.meter_register_id == meter_register_id]

    def list_for_meter_point(self, _meter_point_id):
        return self._readings

    def list_for_building(self, _building_id):
        return self._readings


def test_analytics_calculates_consumption_and_cost() -> None:
    register_id = uuid4()
    readings = [
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc), value=Decimal("10")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 2, 1, tzinfo=timezone.utc), value=Decimal("25")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 3, 1, tzinfo=timezone.utc), value=Decimal("40")),
    ]
    use_case = AnalyticsUseCase(FakeReadingRepository(readings))

    result = use_case.execute_for_meter_register(register_id, Decimal("0.5"))

    assert result.consumption == Decimal("30")
    assert result.cost == Decimal("15.0")
    assert result.scope == "meter_register"


def test_analytics_skips_negative_deltas() -> None:
    register_id = uuid4()
    readings = [
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc), value=Decimal("100")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 2, 1, tzinfo=timezone.utc), value=Decimal("80")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 3, 1, tzinfo=timezone.utc), value=Decimal("110")),
    ]
    use_case = AnalyticsUseCase(FakeReadingRepository(readings))

    result = use_case.execute_for_meter_register(register_id, Decimal("0.5"))

    assert result.consumption == Decimal("30")
    assert result.cost == Decimal("15.0")
