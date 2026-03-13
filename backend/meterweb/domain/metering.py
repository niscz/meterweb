from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from statistics import median
from uuid import UUID, uuid4


class MeteringDomainError(ValueError):
    """Base error for metering business rule violations."""


class NegativeDifferenceError(MeteringDomainError):
    """Raised when an absolute meter reading goes backwards without rollover."""


@dataclass(frozen=True, slots=True)
class Building:
    id: UUID
    name: str

    @classmethod
    def create(cls, name: str) -> "Building":
        cleaned = name.strip()
        if not cleaned:
            raise MeteringDomainError("Building name must not be empty.")
        return cls(id=uuid4(), name=cleaned)


@dataclass(frozen=True, slots=True)
class Unit:
    id: UUID
    building_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class MeterPoint:
    id: UUID
    unit_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class MeterDevice:
    id: UUID
    meter_point_id: UUID
    serial_number: str
    installed_at: datetime
    removed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MeterRegister:
    id: UUID
    meter_device_id: UUID
    code: str
    measurement_unit: str
    rollover_limit: Decimal | None = None


@dataclass(frozen=True, slots=True)
class Reading:
    id: UUID
    meter_register_id: UUID
    measured_at: datetime
    value: Decimal


@dataclass(frozen=True, slots=True)
class MeterReplacement:
    meter_point_id: UUID
    old_device_id: UUID
    new_device_id: UUID
    replaced_at: datetime
    old_device_final_value: Decimal
    new_device_start_value: Decimal


@dataclass(frozen=True, slots=True)
class RollOver:
    meter_register_id: UUID
    occurred_at: datetime
    previous_value: Decimal
    current_value: Decimal
    rollover_limit: Decimal


@dataclass(frozen=True, slots=True)
class RawReading:
    meter_register_id: UUID
    measured_at: datetime
    value: Decimal
    source: str


@dataclass(frozen=True, slots=True)
class IntervalSample:
    start_at: datetime
    end_at: datetime
    value: Decimal


@dataclass(frozen=True, slots=True)
class AggregateConsumption:
    meter_register_id: UUID
    period_start: datetime
    period_end: datetime
    consumption: Decimal


def consumption_from_absolute_readings(
    previous_value: Decimal,
    current_value: Decimal,
    rollover_limit: Decimal | None = None,
) -> Decimal:
    if current_value >= previous_value:
        return current_value - previous_value

    if rollover_limit is None:
        raise NegativeDifferenceError(
            "Current reading is lower than previous reading without rollover."
        )

    if rollover_limit <= previous_value:
        raise MeteringDomainError("Rollover limit must be greater than previous value.")

    return (rollover_limit - previous_value) + current_value


def consumption_from_pulses(pulse_delta: int, pulse_factor: Decimal) -> Decimal:
    if pulse_delta < 0:
        raise MeteringDomainError("Pulse delta must not be negative.")
    if pulse_factor <= Decimal("0"):
        raise MeteringDomainError("Pulse factor must be positive.")
    return Decimal(pulse_delta) * pulse_factor


def aggregate_intervals(
    meter_register_id: UUID,
    period_start: datetime,
    period_end: datetime,
    samples: list[IntervalSample],
) -> AggregateConsumption:
    if period_end <= period_start:
        raise MeteringDomainError("Aggregate period end must be after period start.")

    total = sum((sample.value for sample in samples), start=Decimal("0"))
    return AggregateConsumption(
        meter_register_id=meter_register_id,
        period_start=period_start,
        period_end=period_end,
        consumption=total,
    )


def is_jump(delta: Decimal, max_expected_delta: Decimal) -> bool:
    if delta < Decimal("0"):
        raise MeteringDomainError("Delta must not be negative.")
    if max_expected_delta < Decimal("0"):
        raise MeteringDomainError("Max expected delta must not be negative.")
    return delta > max_expected_delta


def is_standstill(deltas: list[Decimal], tolerance: Decimal = Decimal("0")) -> bool:
    if tolerance < Decimal("0"):
        raise MeteringDomainError("Tolerance must not be negative.")
    return all(abs(delta) <= tolerance for delta in deltas)


def is_outlier(values: list[Decimal], candidate: Decimal, multiplier: Decimal = Decimal("1.5")) -> bool:
    if len(values) < 4:
        return False

    sorted_values = sorted(values)
    mid = len(sorted_values) // 2
    lower_half = sorted_values[:mid]
    upper_half = sorted_values[mid:] if len(sorted_values) % 2 == 0 else sorted_values[mid + 1 :]

    q1 = Decimal(str(median(lower_half)))
    q3 = Decimal(str(median(upper_half)))
    iqr = q3 - q1
    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)
    return candidate < lower_bound or candidate > upper_bound
