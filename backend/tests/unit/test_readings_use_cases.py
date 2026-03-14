from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import meterweb.application.use_cases.readings as readings_module
from meterweb.application.dto import PhotoReadingCreateDTO, ReadingCreateDTO
from meterweb.application.use_cases.readings import AddPhotoReadingUseCase, AddReadingUseCase


@dataclass
class _FakeReading:
    id: UUID
    measured_at: datetime
    value: Decimal


class _FakeReadingRepository:
    def add_manual(self, _meter_register_id: UUID, measured_at: datetime, value: Decimal) -> _FakeReading:
        return _FakeReading(id=uuid4(), measured_at=measured_at, value=value)

    def add_photo(self, _meter_register_id: UUID, measured_at: datetime, value: Decimal, _image_path: str, _ocr_confidence: float) -> _FakeReading:
        return _FakeReading(id=uuid4(), measured_at=measured_at, value=value)


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
