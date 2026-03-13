from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from meterweb.application.ports import BuildingRepository
from meterweb.domain.building import Building, BuildingName
from meterweb.infrastructure.sqlalchemy_models import BuildingRecord


class SqlAlchemyBuildingRepository(BuildingRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, building: Building) -> None:
        self._session.add(BuildingRecord(id=str(building.id), name=building.name.value))
        self._session.commit()

    def list_all(self) -> list[Building]:
        rows = self._session.scalars(select(BuildingRecord).order_by(BuildingRecord.name)).all()
        return [
            Building(id=UUID(row.id), name=BuildingName(row.name))
            for row in rows
        ]
