from fastapi import Depends
from sqlalchemy.orm import Session

from meterweb.application.use_cases import (
    CreateBuildingUseCase,
    ListBuildingsUseCase,
    LoginUseCase,
)
from meterweb.application.ports import ChartAdapter, OCRProvider, ReportRenderer, WeatherProvider
from meterweb.infrastructure.auth import EnvAuthenticator
from meterweb.infrastructure.db import get_session
from meterweb.infrastructure.providers import ProviderConfig, ProviderFactory
from meterweb.infrastructure.repositories import SqlAlchemyBuildingRepository


def get_login_use_case() -> LoginUseCase:
    return LoginUseCase(EnvAuthenticator())


def get_provider_factory() -> ProviderFactory:
    return ProviderFactory(ProviderConfig.from_env())


def get_weather_provider(
    factory: ProviderFactory = Depends(get_provider_factory),
) -> WeatherProvider:
    return factory.create_weather_provider()


def get_ocr_provider(
    factory: ProviderFactory = Depends(get_provider_factory),
) -> OCRProvider:
    return factory.create_ocr_provider()


def get_chart_adapter(
    factory: ProviderFactory = Depends(get_provider_factory),
) -> ChartAdapter:
    return factory.create_chart_adapter()


def get_report_renderer(
    factory: ProviderFactory = Depends(get_provider_factory),
) -> ReportRenderer:
    return factory.create_report_renderer()


def get_create_building_use_case(
    session: Session = Depends(get_session),
) -> CreateBuildingUseCase:
    return CreateBuildingUseCase(SqlAlchemyBuildingRepository(session))


def get_list_buildings_use_case(
    session: Session = Depends(get_session),
) -> ListBuildingsUseCase:
    return ListBuildingsUseCase(SqlAlchemyBuildingRepository(session))
