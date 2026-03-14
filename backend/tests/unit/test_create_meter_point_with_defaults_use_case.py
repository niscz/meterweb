from uuid import UUID

import pytest

from meterweb.application.dto import MeterPointCreateDTO
from meterweb.application.use_cases.buildings import CreateMeterPointWithDefaultDeviceUseCase


class _FakeMeterPointRepository:
    def __init__(self) -> None:
        self.saved = []

    def add(self, meter_point) -> None:  # type: ignore[no-untyped-def]
        self.saved.append(meter_point)


class _FakeMeterDeviceRepository:
    def __init__(self) -> None:
        self.created_for = []
        self.device_id = UUID("11111111-1111-1111-1111-111111111111")

    def add_default_for_meter_point(self, meter_point_id: UUID) -> UUID:
        self.created_for.append(meter_point_id)
        return self.device_id


class _FakeMeterRegisterRepository:
    def __init__(self) -> None:
        self.created_for = []

    def add_default_for_device(self, meter_device_id: UUID) -> UUID:
        self.created_for.append(meter_device_id)
        return UUID("22222222-2222-2222-2222-222222222222")


class _FakeUnitOfWork:
    def __init__(self) -> None:
        self.meter_point_repository = _FakeMeterPointRepository()
        self.meter_device_repository = _FakeMeterDeviceRepository()
        self.meter_register_repository = _FakeMeterRegisterRepository()
        self.begin_called = 0
        self.commit_called = 0
        self.rollback_called = 0

    def begin(self) -> None:
        self.begin_called += 1

    def commit(self) -> None:
        self.commit_called += 1

    def rollback(self) -> None:
        self.rollback_called += 1


class _FailingMeterDeviceRepository(_FakeMeterDeviceRepository):
    def add_default_for_meter_point(self, meter_point_id: UUID) -> UUID:
        raise RuntimeError("boom")


def test_creates_meter_point_with_default_device_and_register() -> None:
    uow = _FakeUnitOfWork()
    use_case = CreateMeterPointWithDefaultDeviceUseCase(uow)  # type: ignore[arg-type]

    result = use_case.execute(
        MeterPointCreateDTO(
            unit_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            name="Strom",
        )
    )

    assert uow.begin_called == 1
    assert uow.commit_called == 1
    assert uow.rollback_called == 0
    assert len(uow.meter_point_repository.saved) == 1
    assert uow.meter_device_repository.created_for == [result.id]
    assert uow.meter_register_repository.created_for == [uow.meter_device_repository.device_id]


def test_rolls_back_when_default_device_creation_fails() -> None:
    uow = _FakeUnitOfWork()
    uow.meter_device_repository = _FailingMeterDeviceRepository()
    use_case = CreateMeterPointWithDefaultDeviceUseCase(uow)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="boom"):
        use_case.execute(
            MeterPointCreateDTO(
                unit_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                name="Wasser",
            )
        )

    assert uow.begin_called == 1
    assert uow.commit_called == 0
    assert uow.rollback_called == 1
