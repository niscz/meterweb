from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from meterweb.application.use_cases import (
    ProcessAbsoluteReadingUseCase,
    ProcessIntervalReadingUseCase,
    ProcessPulseReadingUseCase,
)


def test_process_absolute_reading_use_case_supports_rollover() -> None:
    use_case = ProcessAbsoluteReadingUseCase()
    assert use_case.compute_consumption(Decimal("9998"), Decimal("3"), Decimal("10000")) == Decimal("5")


def test_process_pulse_reading_use_case() -> None:
    use_case = ProcessPulseReadingUseCase()
    assert use_case.compute_consumption(200, Decimal("0.01")) == Decimal("2.00")


def test_process_interval_reading_use_case() -> None:
    use_case = ProcessIntervalReadingUseCase()
    register_id = uuid4()
    period_start = datetime(2025, 2, 1, 0, tzinfo=timezone.utc)
    period_end = datetime(2025, 2, 1, 2, tzinfo=timezone.utc)

    total = use_case.compute_consumption(
        meter_register_id=register_id,
        period_start=period_start,
        period_end=period_end,
        interval_values=[
            (period_start, datetime(2025, 2, 1, 1, tzinfo=timezone.utc), Decimal("0.4")),
            (datetime(2025, 2, 1, 1, tzinfo=timezone.utc), period_end, Decimal("0.6")),
        ],
    )

    assert total == Decimal("1.0")
