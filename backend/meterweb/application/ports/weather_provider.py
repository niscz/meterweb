from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class WeatherSnapshot:
    date: date
    temperature_c: float
    cloud_cover_percent: float


@dataclass(frozen=True)
class WeatherSeriesPoint:
    timestamp: str
    temperature_c: float
    cloud_cover_percent: float


class WeatherProvider(ABC):
    @abstractmethod
    def find_station(self, latitude: float, longitude: float) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_daily_snapshot(self, latitude: float, longitude: float, day: date, station_id: str | None = None) -> WeatherSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get_series(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        resolution: str,
        station_id: str | None = None,
    ) -> list[WeatherSeriesPoint]:
        raise NotImplementedError
