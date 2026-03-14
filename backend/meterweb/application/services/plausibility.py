from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from meterweb.application.ports import ReadingRepository
from meterweb.domain.metering import evaluate_plausibility


@dataclass(frozen=True, slots=True)
class ReadingPlausibilityResult:
    plausible: bool
    warning: str | None


def evaluate_reading_plausibility(
    repository: ReadingRepository,
    meter_register_id: UUID,
    ocr_confidence: float | None,
) -> ReadingPlausibilityResult:
    readings = repository.list_for_meter_register(meter_register_id)
    if len(readings) < 2:
        return ReadingPlausibilityResult(plausible=True, warning=None)

    previous = readings[-2]
    current = readings[-1]
    deltas = [
        next_reading.value - prev_reading.value
        for prev_reading, next_reading in zip(readings, readings[1:])
        if next_reading.value >= prev_reading.value
    ]
    plausibility = evaluate_plausibility(
        previous.value,
        current.value,
        historical_deltas=deltas[:-1] if deltas else [],
        max_expected_delta=Decimal("50000"),
        standstill_tolerance=Decimal("0.001"),
    )

    warning = None
    if ocr_confidence is not None and ocr_confidence < 0.55:
        warning = "OCR confidence is low"

    return ReadingPlausibilityResult(
        plausible=plausibility.is_plausible and warning is None,
        warning=warning,
    )
