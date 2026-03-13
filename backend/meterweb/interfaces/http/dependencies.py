from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session

from meterweb.application.use_cases import (
    AddPhotoReadingUseCase,
    AddReadingUseCase,
    AnalyticsUseCase,
    CreateBuildingUseCase,
    CreateMeterPointUseCase,
    CreateUnitUseCase,
    ExportUseCase,
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
    LoginUseCase,
    OCRRunUseCase,
    WeatherSyncUseCase,
)
from meterweb.application.ports import ChartAdapter, OCRProvider, ReportRenderer, WeatherProvider
from meterweb.infrastructure.auth import EnvAuthenticator
from meterweb.infrastructure.db import get_session
from meterweb.infrastructure.providers import ProviderConfig, ProviderFactory
from meterweb.infrastructure.repositories import (
    JsonWeatherStationRepository,
    SqlAlchemyBuildingRepository,
    SqlAlchemyMeterPointRepository,
    SqlAlchemyReadingRepository,
    SqlAlchemyUnitRepository,
)


def get_login_use_case() -> LoginUseCase:
    return LoginUseCase(EnvAuthenticator())


def get_provider_factory() -> ProviderFactory:
    return ProviderFactory(ProviderConfig.from_env())


def get_weather_provider(factory: ProviderFactory = Depends(get_provider_factory)) -> WeatherProvider:
    return factory.create_weather_provider()


def get_ocr_provider(factory: ProviderFactory = Depends(get_provider_factory)) -> OCRProvider:
    return factory.create_ocr_provider()


def get_chart_adapter(factory: ProviderFactory = Depends(get_provider_factory)) -> ChartAdapter:
    return factory.create_chart_adapter()


def get_report_renderer(factory: ProviderFactory = Depends(get_provider_factory)) -> ReportRenderer:
    return factory.create_report_renderer()


def get_create_building_use_case(session: Session = Depends(get_session)) -> CreateBuildingUseCase:
    return CreateBuildingUseCase(SqlAlchemyBuildingRepository(session))


def get_list_buildings_use_case(session: Session = Depends(get_session)) -> ListBuildingsUseCase:
    return ListBuildingsUseCase(SqlAlchemyBuildingRepository(session))


def get_create_unit_use_case(session: Session = Depends(get_session)) -> CreateUnitUseCase:
    return CreateUnitUseCase(SqlAlchemyUnitRepository(session))


def get_list_units_use_case(session: Session = Depends(get_session)) -> ListUnitsUseCase:
    return ListUnitsUseCase(SqlAlchemyUnitRepository(session))


def get_create_meter_point_use_case(session: Session = Depends(get_session)) -> CreateMeterPointUseCase:
    return CreateMeterPointUseCase(SqlAlchemyMeterPointRepository(session))


def get_list_meter_points_use_case(session: Session = Depends(get_session)) -> ListMeterPointsUseCase:
    return ListMeterPointsUseCase(SqlAlchemyMeterPointRepository(session))


def get_add_reading_use_case(session: Session = Depends(get_session)) -> AddReadingUseCase:
    return AddReadingUseCase(SqlAlchemyReadingRepository(session))


def get_ocr_run_use_case(ocr_provider: OCRProvider = Depends(get_ocr_provider)) -> OCRRunUseCase:
    return OCRRunUseCase(ocr_provider)


def get_add_photo_reading_use_case(
    session: Session = Depends(get_session),
    ocr_use_case: OCRRunUseCase = Depends(get_ocr_run_use_case),
) -> AddPhotoReadingUseCase:
    return AddPhotoReadingUseCase(SqlAlchemyReadingRepository(session), ocr_use_case)


def get_export_use_case(
    session: Session = Depends(get_session),
    report_renderer: ReportRenderer = Depends(get_report_renderer),
) -> ExportUseCase:
    return ExportUseCase(SqlAlchemyReadingRepository(session), report_renderer)


def get_weather_sync_use_case(weather_provider: WeatherProvider = Depends(get_weather_provider)) -> WeatherSyncUseCase:
    return build_weather_sync_use_case(weather_provider)


def build_weather_sync_use_case(weather_provider: WeatherProvider) -> WeatherSyncUseCase:
    station_repository = JsonWeatherStationRepository(Path("/data/weather_station_overrides.json"))
    return WeatherSyncUseCase(weather_provider, station_repository)


def get_analytics_use_case(session: Session = Depends(get_session)) -> AnalyticsUseCase:
    return AnalyticsUseCase(SqlAlchemyReadingRepository(session))
