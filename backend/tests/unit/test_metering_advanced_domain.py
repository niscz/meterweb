from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from meterweb.domain.metering import (
    IntervalSample,
    MeterDeviceHistoryEvent,
    MeterReplacement,
    RawIntervalReading,
    RawPulseReading,
    RegisterTariffBinding,
    RollOver,
    aggregate_intervals,
    consumption_from_absolute_readings,
    evaluate_plausibility,
)


def test_rollover_and_event_models_capture_history() -> None:
    register_id = uuid4()
    meter_point_id = uuid4()
    old_device_id = uuid4()
    new_device_id = uuid4()
    occurred_at = datetime(2025, 3, 1, tzinfo=timezone.utc)

    replacement = MeterReplacement(
        meter_point_id=meter_point_id,
        old_device_id=old_device_id,
        new_device_id=new_device_id,
        replaced_at=occurred_at,
        old_device_final_value=Decimal("9999"),
        new_device_start_value=Decimal("0"),
    )
    history_event = MeterDeviceHistoryEvent(
        meter_point_id=meter_point_id,
        device_id=new_device_id,
        event_type="replaced",
        occurred_at=occurred_at,
        note="Planned exchange",
    )
    rollover = RollOver(
        meter_register_id=register_id,
        occurred_at=occurred_at,
        previous_value=Decimal("9999"),
        current_value=Decimal("5"),
        rollover_limit=Decimal("10000"),
    )

    assert replacement.new_device_start_value == Decimal("0")
    assert history_event.event_type == "replaced"
    assert consumption_from_absolute_readings(
        rollover.previous_value,
        rollover.current_value,
        rollover.rollover_limit,
    ) == Decimal("6")


def test_multi_register_tariff_and_raw_paths() -> None:
    register_id = uuid4()
    binding = RegisterTariffBinding(
        meter_register_id=register_id,
        tariff_code="HT",
        valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
        valid_to=None,
    )
    pulse = RawPulseReading(
        meter_register_id=register_id,
        measured_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
        pulse_count=150,
        pulse_factor=Decimal("0.01"),
        source="gateway",
    )
    interval = RawIntervalReading(
        meter_register_id=register_id,
        start_at=datetime(2025, 1, 2, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 1, 2, 1, tzinfo=timezone.utc),
        value=Decimal("1.23"),
        source="smart_meter",
    )

    aggregate = aggregate_intervals(
        meter_register_id=register_id,
        period_start=interval.start_at,
        period_end=interval.end_at,
        samples=[IntervalSample(interval.start_at, interval.end_at, interval.value)],
    )

    assert binding.tariff_code == "HT"
    assert pulse.pulse_count == 150
    assert aggregate.consumption == Decimal("1.23")


def test_plausibility_detects_ocr_and_weather_conflicts() -> None:
    result = evaluate_plausibility(
        previous_value=Decimal("100"),
        current_value=Decimal("170"),
        historical_deltas=[Decimal("10"), Decimal("11"), Decimal("12"), Decimal("9")],
        max_expected_delta=Decimal("40"),
        weather_expected_range=(Decimal("0"), Decimal("50")),
        ocr_confidence=Decimal("0.45"),
    )

    assert result.is_plausible is False
    assert "jump" in result.flags
    assert "weather_conflict" in result.flags
    assert "ocr_conflict" in result.flags
