import json
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from meterweb.application.ports import WeatherProvider, WeatherSnapshot


class BrightSkyWeatherProvider(WeatherProvider):
    def __init__(self, cache_dir: Path, timeout_seconds: float = 5.0) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._timeout_seconds = timeout_seconds

    def get_daily_snapshot(self, latitude: float, longitude: float, day: date) -> WeatherSnapshot:
        cache_file = self._cache_file(latitude, longitude, day)
        if cache_file.exists():
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            return WeatherSnapshot(
                date=date.fromisoformat(payload["date"]),
                temperature_c=payload["temperature_c"],
                cloud_cover_percent=payload["cloud_cover_percent"],
            )

        params = urlencode(
            {
                "lat": latitude,
                "lon": longitude,
                "date": day.isoformat(),
                "last_date": day.isoformat(),
            }
        )
        url = f"https://api.brightsky.dev/weather?{params}"
        with urlopen(url, timeout=self._timeout_seconds) as response:  # noqa: S310
            data = json.load(response)

        weather_entries = data.get("weather", [])
        if not weather_entries:
            raise ValueError("Keine Wetterdaten von Bright Sky verfügbar.")

        temperatures = [entry.get("temperature") for entry in weather_entries if entry.get("temperature") is not None]
        if not temperatures:
            raise ValueError("Keine Temperaturdaten von Bright Sky verfügbar.")

        cloud_cover = [entry.get("cloud_cover") for entry in weather_entries if entry.get("cloud_cover") is not None]
        snapshot = WeatherSnapshot(
            date=day,
            temperature_c=sum(temperatures) / len(temperatures),
            cloud_cover_percent=(sum(cloud_cover) / len(cloud_cover)) if cloud_cover else 0.0,
        )
        cache_payload = {
            "date": snapshot.date.isoformat(),
            "temperature_c": snapshot.temperature_c,
            "cloud_cover_percent": snapshot.cloud_cover_percent,
        }
        cache_file.write_text(json.dumps(cache_payload), encoding="utf-8")
        return snapshot

    def _cache_file(self, latitude: float, longitude: float, day: date) -> Path:
        key = f"{latitude:.4f}_{longitude:.4f}_{day.isoformat()}.json"
        return self._cache_dir / key
