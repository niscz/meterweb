from sqlalchemy.orm import Session

from meterweb.application.ports import UnitOfWork
from meterweb.infrastructure.repositories import (
    SqlAlchemyBuildingRepository,
    SqlAlchemyMeterDeviceRepository,
    SqlAlchemyMeterPointRepository,
    SqlAlchemyMeterRegisterRepository,
    SqlAlchemyReadingRepository,
    SqlAlchemyUnitRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: Session) -> None:
        self._session = session
        self.building_repository = SqlAlchemyBuildingRepository(session)
        self.unit_repository = SqlAlchemyUnitRepository(session)
        self.meter_point_repository = SqlAlchemyMeterPointRepository(session)
        self.meter_device_repository = SqlAlchemyMeterDeviceRepository(session)
        self.meter_register_repository = SqlAlchemyMeterRegisterRepository(session)
        self.reading_repository = SqlAlchemyReadingRepository(session)

    def begin(self) -> None:
        self._session.begin()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
