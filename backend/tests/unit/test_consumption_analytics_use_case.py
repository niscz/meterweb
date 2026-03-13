from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from meterweb.application.use_cases import AnalyticsUseCase
from meterweb.domain.metering import Reading


class FakeReadingRepository:
    def __init__(self, readings: list[Reading]):
        self._readings = readings

    def add_manual(self, meter_point_id, measured_at, value):
        raise NotImplementedError

    def list_for_meter_point(self, meter_point_id):
        return self._readings


def test_analytics_calculates_consumption_and_cost() -> None:
    register_id = uuid4()
    readings = [
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc), value=Decimal("10")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 2, 1, tzinfo=timezone.utc), value=Decimal("25")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 3, 1, tzinfo=timezone.utc), value=Decimal("40")),
    ]
    use_case = AnalyticsUseCase(FakeReadingRepository(readings))

    result = use_case.execute(uuid4(), Decimal("0.5"))

    assert result.consumption == Decimal("30")
    assert result.cost == Decimal("15.0")


def test_analytics_skips_negative_deltas() -> None:
    register_id = uuid4()
    readings = [
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc), value=Decimal("100")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 2, 1, tzinfo=timezone.utc), value=Decimal("80")),
        Reading(id=uuid4(), meter_register_id=register_id, measured_at=datetime(2025, 3, 1, tzinfo=timezone.utc), value=Decimal("110")),
    ]
    use_case = AnalyticsUseCase(FakeReadingRepository(readings))

    result = use_case.execute(uuid4(), Decimal("0.5"))

    assert result.consumption == Decimal("30")
    assert result.cost == Decimal("15.0")
