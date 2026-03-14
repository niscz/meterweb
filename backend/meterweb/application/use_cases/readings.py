import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from meterweb.application.dto import (
    OCRCandidateDTO,
    OCRDecisionDTO,
    OCRRunResultDTO,
    PhotoReadingCreateDTO,
    ReadingCreateDTO,
    ReadingOCRMetadataDTO,
    ReadingViewDTO,
)
from meterweb.application.ports import OCRProvider, UnitOfWork
from meterweb.application.services.plausibility import (
    ReadingPlausibilityResult,
    evaluate_reading_plausibility,
)
from meterweb.domain.metering import (
    IntervalSample,
    aggregate_intervals,
    consumption_from_absolute_readings,
    consumption_from_pulses,
)


class AddReadingUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: ReadingCreateDTO) -> ReadingViewDTO:
        measured_at = data.measured_at
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)
        self._uow.begin()
        try:
            created = self._uow.reading_repository.add_manual(data.meter_register_id, measured_at, data.value)
            self._uow.commit()
        except Exception:
            self._uow.rollback()
            raise

        plausibility = evaluate_reading_plausibility(
            self._uow.reading_repository,
            data.meter_register_id,
            ocr_confidence=None,
        )
        return ReadingViewDTO(
            id=created.id,
            meter_register_id=data.meter_register_id,
            measured_at=created.measured_at,
            value=created.value,
            plausible=plausibility.plausible,
        )


class OCRRunUseCase:
    def __init__(self, provider: OCRProvider) -> None:
        self._provider = provider

    def execute(self, image_path: Path) -> OCRRunResultDTO:
        result = self._provider.extract_text(image_path)
        candidates: list[OCRCandidateDTO] = []
        best_score = (-1, -1, Decimal("-1"))
        best_candidate = None
        for token in re.findall(r"\d+(?:[\.,]\d+)?", result.text):
            normalized = token.replace(",", ".")
            try:
                candidate = OCRCandidateDTO(
                    value=Decimal(normalized),
                    confidence=result.confidence,
                )
            except Exception:
                continue
            candidates.append(candidate)
            score = self._candidate_score(candidate)
            if score > best_score:
                best_score = score
                best_candidate = candidate
        return OCRRunResultDTO(
            text=result.text,
            candidates=candidates,
            best_candidate=best_candidate,
        )

    @staticmethod
    def _candidate_score(candidate: OCRCandidateDTO) -> tuple[int, int, Decimal]:
        value = candidate.value
        is_integer = int(value == value.to_integral_value())
        digit_count = len(value.as_tuple().digits)
        return is_integer, digit_count, value


class AddPhotoReadingUseCase:
    def __init__(self, uow: UnitOfWork, ocr_use_case: OCRRunUseCase) -> None:
        self._uow = uow
        self._ocr_use_case = ocr_use_case

    def execute(
        self,
        data: PhotoReadingCreateDTO,
        confirmed_value: Decimal | None = None,
    ) -> tuple[ReadingViewDTO, OCRRunResultDTO, ReadingPlausibilityResult]:
        measured_at = data.measured_at
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)

        ocr_result = self._ocr_use_case.execute(Path(data.image_path))
        value = confirmed_value if confirmed_value is not None else (
            ocr_result.best_candidate.value if ocr_result.best_candidate else None
        )
        if value is None:
            raise ValueError("Kein OCR-Kandidat erkannt. Bitte Wert manuell bestätigen.")

        ocr_confidence = (
            ocr_result.best_candidate.confidence
            if ocr_result.best_candidate
            else 0.0
        )
        self._uow.begin()
        try:
            created = self._uow.reading_repository.add_photo(
                data.meter_register_id,
                measured_at,
                value,
                data.image_path,
                ocr_confidence,
                ocr_result.text,
                ocr_result.candidates,
                ocr_status="suggested",
            )
            self._uow.commit()
        except Exception:
            self._uow.rollback()
            raise

        try:
            plausibility = evaluate_reading_plausibility(
                self._uow.reading_repository,
                data.meter_register_id,
                ocr_confidence=ocr_confidence,
            )
        except Exception:
            plausibility = ReadingPlausibilityResult(plausible=True, warning=None)
        return (
            ReadingViewDTO(
                id=created.id,
                meter_register_id=data.meter_register_id,
                measured_at=created.measured_at,
                value=created.value,
                plausible=plausibility.plausible,
            ),
            ocr_result,
            plausibility,
        )


class ConfirmReadingUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: OCRDecisionDTO) -> ReadingViewDTO:
        self._uow.begin()
        try:
            reading = self._uow.reading_repository.update_ocr_status(data.reading_id, status="confirmed")
            self._uow.commit()
        except Exception:
            self._uow.rollback()
            raise
        plausibility = evaluate_reading_plausibility(self._uow.reading_repository, reading.meter_register_id, ocr_confidence=None)
        return ReadingViewDTO(id=reading.id, meter_register_id=reading.meter_register_id, measured_at=reading.measured_at, value=reading.value, plausible=plausibility.plausible)


class CorrectReadingUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: OCRDecisionDTO) -> ReadingViewDTO:
        if data.value is None:
            raise ValueError("Korrigierter Wert erforderlich.")
        self._uow.begin()
        try:
            reading = self._uow.reading_repository.update_ocr_status(data.reading_id, status="corrected", corrected_value=data.value)
            self._uow.commit()
        except Exception:
            self._uow.rollback()
            raise
        plausibility = evaluate_reading_plausibility(self._uow.reading_repository, reading.meter_register_id, ocr_confidence=None)
        return ReadingViewDTO(id=reading.id, meter_register_id=reading.meter_register_id, measured_at=reading.measured_at, value=reading.value, plausible=plausibility.plausible)


class OCRAcceptUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: OCRDecisionDTO) -> ReadingOCRMetadataDTO:
        self._uow.begin()
        try:
            self._uow.reading_repository.update_ocr_status(data.reading_id, status="accepted")
            metadata = self._uow.reading_repository.get_ocr_metadata(data.reading_id)
            self._uow.commit()
        except Exception:
            self._uow.rollback()
            raise
        return metadata


class OCRRejectUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: OCRDecisionDTO) -> ReadingOCRMetadataDTO:
        self._uow.begin()
        try:
            self._uow.reading_repository.update_ocr_status(data.reading_id, status="rejected")
            metadata = self._uow.reading_repository.get_ocr_metadata(data.reading_id)
            self._uow.commit()
        except Exception:
            self._uow.rollback()
            raise
        return metadata


class ProcessAbsoluteReadingUseCase:
    def compute_consumption(
        self,
        previous_value: Decimal,
        current_value: Decimal,
        rollover_limit: Decimal | None = None,
    ) -> Decimal:
        return consumption_from_absolute_readings(
            previous_value,
            current_value,
            rollover_limit,
        )


class ProcessPulseReadingUseCase:
    def compute_consumption(self, pulse_delta: int, pulse_factor: Decimal) -> Decimal:
        return consumption_from_pulses(pulse_delta, pulse_factor)


class ProcessIntervalReadingUseCase:
    def compute_consumption(
        self,
        meter_register_id: UUID,
        period_start: datetime,
        period_end: datetime,
        interval_values: list[tuple[datetime, datetime, Decimal]],
    ) -> Decimal:
        aggregate = aggregate_intervals(
            meter_register_id=meter_register_id,
            period_start=period_start,
            period_end=period_end,
            samples=[
                IntervalSample(start_at=start_at, end_at=end_at, value=value)
                for start_at, end_at, value in interval_values
            ],
        )
        return aggregate.consumption
