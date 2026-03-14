from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import meterweb.application.use_cases.readings as readings_module
from meterweb.application.dto import OCRCandidateDTO, OCRDecisionDTO, PhotoReadingCreateDTO, ReadingCreateDTO
from meterweb.application.services.plausibility import PLAUSIBILITY_UNAVAILABLE_WARNING
from meterweb.application.use_cases.readings import (
    AddPhotoReadingUseCase,
    AddReadingUseCase,
    ConfirmReadingUseCase,
    CorrectReadingUseCase,
    OCRAcceptUseCase,
    OCRRejectUseCase,
)


@dataclass
class _FakeReading:
    id: UUID
    meter_register_id: UUID
    measured_at: datetime
    value: Decimal


class _FakeReadingRepository:
    def __init__(self) -> None:
        self.last_status = "suggested"

    def add_manual(self, _meter_register_id: UUID, measured_at: datetime, value: Decimal) -> _FakeReading:
        return _FakeReading(id=uuid4(), meter_register_id=_meter_register_id, measured_at=measured_at, value=value)

    def add_photo(
        self,
        _meter_register_id: UUID,
        measured_at: datetime,
        value: Decimal,
        _image_path: str,
        _ocr_confidence: float,
        _ocr_text: str,
        _ocr_candidates: list[OCRCandidateDTO],
        ocr_status: str = "suggested",
    ) -> _FakeReading:
        return _FakeReading(id=uuid4(), meter_register_id=_meter_register_id, measured_at=measured_at, value=value)

    def update_ocr_status(self, reading_id: UUID, *, status: str, corrected_value: Decimal | None = None) -> _FakeReading:
        self.last_status = status
        return _FakeReading(
            id=reading_id,
            meter_register_id=uuid4(),
            measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            value=corrected_value or Decimal("123"),
        )

    def list_for_meter_register(self, _meter_register_id: UUID):
        return [
            _FakeReading(
                id=uuid4(),
                meter_register_id=_meter_register_id,
                measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                value=Decimal("100"),
            ),
            _FakeReading(
                id=uuid4(),
                meter_register_id=_meter_register_id,
                measured_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
                value=Decimal("123"),
            ),
        ]

    def get_ocr_metadata(self, _reading_id: UUID):
        return SimpleNamespace(
            image_path="/tmp/mock.jpg",
            ocr_confidence=0.9,
            ocr_text="123",
            ocr_candidates=[OCRCandidateDTO(value=Decimal("123"), confidence=0.9)],
            ocr_status=self.last_status,
        )


class _FakeUnitOfWork:
    def __init__(self) -> None:
        self.reading_repository = _FakeReadingRepository()
        self.state: list[str] = []

    def begin(self) -> None:
        self.state.append("begin")

    def commit(self) -> None:
        self.state.append("commit")

    def rollback(self) -> None:
        self.state.append("rollback")


class _FakeOCRRunUseCase:
    def execute(self, _image_path):
        return SimpleNamespace(
            text="123",
            best_candidate=SimpleNamespace(value=Decimal("123"), confidence=0.9),
            candidates=[SimpleNamespace(value=Decimal("123"), confidence=0.9)],
        )


def test_add_reading_commits_before_plausibility(monkeypatch) -> None:
    uow = _FakeUnitOfWork()
    observed: dict[str, str | None] = {"state_before_eval": None}

    def _fake_eval(_repo, _meter_register_id, ocr_confidence=None):
        observed["state_before_eval"] = uow.state[-1] if uow.state else None
        assert ocr_confidence is None
        return SimpleNamespace(plausible=False)

    monkeypatch.setattr(readings_module, "evaluate_reading_plausibility", _fake_eval)

    use_case = AddReadingUseCase(uow)
    meter_register_id = uuid4()
    result = use_case.execute(
        ReadingCreateDTO(
            meter_register_id=meter_register_id,
            measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            value=Decimal("42"),
        )
    )

    assert observed["state_before_eval"] == "commit"
    assert result.plausible is False


def test_add_photo_reading_commits_before_plausibility(monkeypatch) -> None:
    uow = _FakeUnitOfWork()
    observed: dict[str, str | None] = {"state_before_eval": None}

    def _fake_eval(_repo, _meter_register_id, ocr_confidence=None):
        observed["state_before_eval"] = uow.state[-1] if uow.state else None
        assert ocr_confidence == 0.9
        return SimpleNamespace(plausible=True, warning=None)

    monkeypatch.setattr(readings_module, "evaluate_reading_plausibility", _fake_eval)

    use_case = AddPhotoReadingUseCase(uow, _FakeOCRRunUseCase())
    meter_register_id = uuid4()
    result, _ocr_result, plausibility = use_case.execute(
        PhotoReadingCreateDTO(
            meter_register_id=meter_register_id,
            measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            image_path="/tmp/mock.jpg",
        )
    )

    assert observed["state_before_eval"] == "commit"
    assert result.plausible is True
    assert plausibility.warning is None


def test_reading_status_transitions() -> None:
    uow = _FakeUnitOfWork()
    reading_id = uuid4()

    confirmed = ConfirmReadingUseCase(uow).execute(OCRDecisionDTO(reading_id=reading_id))
    corrected = CorrectReadingUseCase(uow).execute(OCRDecisionDTO(reading_id=reading_id, value=Decimal("321")))
    accepted = OCRAcceptUseCase(uow).execute(OCRDecisionDTO(reading_id=reading_id))
    rejected = OCRRejectUseCase(uow).execute(OCRDecisionDTO(reading_id=reading_id))

    assert confirmed.value == Decimal("123")
    assert corrected.value == Decimal("321")
    assert accepted.ocr_status == "accepted"
    assert rejected.ocr_status == "rejected"


def test_add_photo_reading_returns_warning_when_plausibility_check_fails(monkeypatch, caplog) -> None:
    uow = _FakeUnitOfWork()

    def _raise_eval(_repo, _meter_register_id, ocr_confidence=None):
        assert uow.state[-1] == "commit"
        raise RuntimeError("temporary repository issue")

    monkeypatch.setattr(readings_module, "evaluate_reading_plausibility", _raise_eval)

    use_case = AddPhotoReadingUseCase(uow, _FakeOCRRunUseCase())
    meter_register_id = uuid4()
    result, _ocr_result, plausibility = use_case.execute(
        PhotoReadingCreateDTO(
            meter_register_id=meter_register_id,
            measured_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            image_path="/tmp/mock.jpg",
        )
    )

    assert result.id is not None
    assert result.plausible is False
    assert plausibility.plausible is False
    assert plausibility.warning == PLAUSIBILITY_UNAVAILABLE_WARNING
    assert "plausibility_check_unavailable" in caplog.text
    assert str(meter_register_id) in caplog.text
    assert str(result.id) in caplog.text
