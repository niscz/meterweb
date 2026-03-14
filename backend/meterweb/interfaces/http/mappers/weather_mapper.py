from meterweb.application.ports.weather_provider import WeatherSeriesPoint


def to_weather_series_item(point: WeatherSeriesPoint) -> dict[str, object]:
    return {
        "timestamp": point.timestamp,
        "temperature_c": point.temperature_c,
        "cloud_cover_percent": point.cloud_cover_percent,
    }
