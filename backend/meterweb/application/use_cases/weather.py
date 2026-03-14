from datetime import date
from uuid import UUID

from meterweb.application.ports import (
    WeatherProvider,
    WeatherSeriesPoint,
    WeatherStationRepository,
)


class WeatherSyncUseCase:
    def __init__(
        self,
        weather_provider: WeatherProvider,
        station_repository: WeatherStationRepository,
    ) -> None:
        self._weather_provider = weather_provider
        self._station_repository = station_repository

    def select_station(
        self,
        building_id: UUID,
        latitude: float,
        longitude: float,
        force_auto: bool = False,
    ) -> str:
        override = None if force_auto else self._station_repository.get_override(building_id)
        station = override or self._weather_provider.find_station(latitude, longitude)
        return station

    def set_manual_station(self, building_id: UUID, station_id: str) -> None:
        self._station_repository.set_override(building_id, station_id)

    def set_auto_station(self, building_id: UUID) -> None:
        self._station_repository.set_override(building_id, None)

    def get_series(
        self,
        building_id: UUID,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        resolution: str,
    ) -> list[WeatherSeriesPoint]:
        station = self.select_station(building_id, latitude, longitude)
        return self._weather_provider.get_series(
            latitude,
            longitude,
            start_date,
            end_date,
            resolution,
            station_id=station,
        )
