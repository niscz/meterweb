from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from meterweb.domain.metering import (
    IntervalSample,
    NegativeDifferenceError,
    aggregate_intervals,
    consumption_from_absolute_readings,
    consumption_from_pulses,
    is_jump,
    is_outlier,
    is_standstill,
)


def test_absolute_reading_negative_diff_without_rollover_raises() -> None:
    with pytest.raises(NegativeDifferenceError):
        consumption_from_absolute_readings(Decimal("120.0"), Decimal("110.0"))


def test_absolute_reading_with_rollover_is_compensated() -> None:
    result = consumption_from_absolute_readings(
        Decimal("9998"), Decimal("4"), rollover_limit=Decimal("10000")
    )
    assert result == Decimal("6")


def test_jump_detection_flags_large_delta() -> None:
    assert is_jump(Decimal("250"), Decimal("100")) is True
    assert is_jump(Decimal("75"), Decimal("100")) is False


def test_standstill_detects_zero_deltas() -> None:
    assert is_standstill([Decimal("0"), Decimal("0.000"), Decimal("0")]) is True
    assert is_standstill([Decimal("0"), Decimal("0.1")]) is False


def test_outlier_logic_uses_iqr() -> None:
    baseline = [Decimal("10"), Decimal("11"), Decimal("10"), Decimal("9"), Decimal("12")]
    assert is_outlier(baseline, Decimal("40")) is True
    assert is_outlier(baseline, Decimal("11")) is False


def test_impulse_and_interval_aggregation() -> None:
    assert consumption_from_pulses(120, Decimal("0.01")) == Decimal("1.20")

    register_id = uuid4()
    period_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    period_end = datetime(2025, 1, 1, 2, tzinfo=timezone.utc)
    aggregate = aggregate_intervals(
        meter_register_id=register_id,
        period_start=period_start,
        period_end=period_end,
        samples=[
            IntervalSample(period_start, datetime(2025, 1, 1, 1, tzinfo=timezone.utc), Decimal("0.40")),
            IntervalSample(datetime(2025, 1, 1, 1, tzinfo=timezone.utc), period_end, Decimal("0.60")),
        ],
    )

    assert aggregate.consumption == Decimal("1.00")
