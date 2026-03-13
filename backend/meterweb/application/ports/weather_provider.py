from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class WeatherSnapshot:
    date: date
    temperature_c: float
    cloud_cover_percent: float


class WeatherProvider(ABC):
    @abstractmethod
    def get_daily_snapshot(self, latitude: float, longitude: float, day: date) -> WeatherSnapshot:
        raise NotImplementedError
