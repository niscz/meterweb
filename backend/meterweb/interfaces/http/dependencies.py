from fastapi import Depends
from sqlalchemy.orm import Session

from meterweb.application.use_cases import (
    CreateBuildingUseCase,
    ListBuildingsUseCase,
    LoginUseCase,
)
from meterweb.infrastructure.auth import EnvAuthenticator
from meterweb.infrastructure.db import get_session
from meterweb.infrastructure.repositories import SqlAlchemyBuildingRepository


def get_login_use_case() -> LoginUseCase:
    return LoginUseCase(EnvAuthenticator())


def get_create_building_use_case(
    session: Session = Depends(get_session),
) -> CreateBuildingUseCase:
    return CreateBuildingUseCase(SqlAlchemyBuildingRepository(session))


def get_list_buildings_use_case(
    session: Session = Depends(get_session),
) -> ListBuildingsUseCase:
    return ListBuildingsUseCase(SqlAlchemyBuildingRepository(session))
