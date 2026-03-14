from sqlalchemy.orm import Session

from meterweb.application.ports import ChartAdapter, OCRProvider, ReportRenderer, WeatherProvider
from meterweb.application.use_cases.analytics import AnalyticsUseCase
from meterweb.application.use_cases.auth import LoginUseCase
from meterweb.application.use_cases.buildings import (
    CreateBuildingUseCase,
    CreateMeterPointUseCase,
    CreateUnitUseCase,
    ListBuildingsUseCase,
    ListMeterPointsUseCase,
    ListUnitsUseCase,
)
from meterweb.application.use_cases.exports import ExportUseCase
from meterweb.application.use_cases.readings import AddPhotoReadingUseCase, AddReadingUseCase, OCRRunUseCase
from meterweb.application.use_cases.weather import WeatherSyncUseCase
from meterweb.infrastructure.auth import EnvAuthenticator
from meterweb.infrastructure.providers import ProviderFactory
from meterweb.infrastructure.repositories import (
    JsonWeatherStationRepository,
    SqlAlchemyBuildingRepository,
    SqlAlchemyMeterPointRepository,
    SqlAlchemyReadingRepository,
    SqlAlchemyUnitRepository,
)
from meterweb.infrastructure.settings import AppSettings


class AppContainer:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._provider_factory = ProviderFactory(self.settings.provider_config())

    @classmethod
    def from_env(cls) -> "AppContainer":
        return cls(AppSettings.from_env())

    def provider_factory(self) -> ProviderFactory:
        return self._provider_factory

    # repository factories
    def building_repository(self, session: Session) -> SqlAlchemyBuildingRepository:
        return SqlAlchemyBuildingRepository(session)

    def unit_repository(self, session: Session) -> SqlAlchemyUnitRepository:
        return SqlAlchemyUnitRepository(session)

    def meter_point_repository(self, session: Session) -> SqlAlchemyMeterPointRepository:
        return SqlAlchemyMeterPointRepository(session)

    def reading_repository(self, session: Session) -> SqlAlchemyReadingRepository:
        return SqlAlchemyReadingRepository(session)

    def weather_station_repository(self) -> JsonWeatherStationRepository:
        return JsonWeatherStationRepository(self.settings.weather_station_overrides_path)

    # provider factories
    def weather_provider(self) -> WeatherProvider:
        return self._provider_factory.create_weather_provider()

    def ocr_provider(self) -> OCRProvider:
        return self._provider_factory.create_ocr_provider()

    def chart_adapter(self) -> ChartAdapter:
        return self._provider_factory.create_chart_adapter()

    def report_renderer(self) -> ReportRenderer:
        return self._provider_factory.create_report_renderer()

    # use case factories
    def login_use_case(self) -> LoginUseCase:
        return LoginUseCase(EnvAuthenticator())

    def create_building_use_case(self, session: Session) -> CreateBuildingUseCase:
        return CreateBuildingUseCase(self.building_repository(session))

    def list_buildings_use_case(self, session: Session) -> ListBuildingsUseCase:
        return ListBuildingsUseCase(self.building_repository(session))

    def create_unit_use_case(self, session: Session) -> CreateUnitUseCase:
        return CreateUnitUseCase(self.unit_repository(session))

    def list_units_use_case(self, session: Session) -> ListUnitsUseCase:
        return ListUnitsUseCase(self.unit_repository(session))

    def create_meter_point_use_case(self, session: Session) -> CreateMeterPointUseCase:
        return CreateMeterPointUseCase(self.meter_point_repository(session))

    def list_meter_points_use_case(self, session: Session) -> ListMeterPointsUseCase:
        return ListMeterPointsUseCase(self.meter_point_repository(session))

    def add_reading_use_case(self, session: Session) -> AddReadingUseCase:
        return AddReadingUseCase(self.reading_repository(session))

    def ocr_run_use_case(self) -> OCRRunUseCase:
        return OCRRunUseCase(self.ocr_provider())

    def add_photo_reading_use_case(self, session: Session) -> AddPhotoReadingUseCase:
        return AddPhotoReadingUseCase(self.reading_repository(session), self.ocr_run_use_case())

    def export_use_case(self, session: Session) -> ExportUseCase:
        return ExportUseCase(self.reading_repository(session), self.report_renderer())

    def weather_sync_use_case(self) -> WeatherSyncUseCase:
        return WeatherSyncUseCase(self.weather_provider(), self.weather_station_repository())

    def analytics_use_case(self, session: Session) -> AnalyticsUseCase:
        return AnalyticsUseCase(self.reading_repository(session))
