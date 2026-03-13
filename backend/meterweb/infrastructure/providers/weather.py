import json
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from meterweb.application.ports import WeatherProvider, WeatherSeriesPoint, WeatherSnapshot


class BrightSkyWeatherProvider(WeatherProvider):
    def __init__(self, cache_dir: Path, timeout_seconds: float = 5.0) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._timeout_seconds = timeout_seconds

    def find_station(self, latitude: float, longitude: float) -> str:
        key = f"station_{latitude:.4f}_{longitude:.4f}.json"
        cache_file = self._cache_dir / key
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))["station_id"]
        station_id = f"AUTO-{latitude:.2f}-{longitude:.2f}"
        cache_file.write_text(json.dumps({"station_id": station_id}), encoding="utf-8")
        return station_id

    def get_daily_snapshot(self, latitude: float, longitude: float, day: date, station_id: str | None = None) -> WeatherSnapshot:
        cache_file = self._cache_file(latitude, longitude, day, station_id)
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
                "dwd_station_id": station_id,
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

    def get_series(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        resolution: str,
        station_id: str | None = None,
    ) -> list[WeatherSeriesPoint]:
        cache_file = self._cache_dir / f"series_{latitude:.4f}_{longitude:.4f}_{start_date.isoformat()}_{end_date.isoformat()}_{resolution}_{station_id or 'auto'}.json"
        if cache_file.exists():
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            return [WeatherSeriesPoint(**item) for item in cached]

        params = urlencode(
            {
                "lat": latitude,
                "lon": longitude,
                "date": start_date.isoformat(),
                "last_date": end_date.isoformat(),
                "dwd_station_id": station_id,
            }
        )
        url = f"https://api.brightsky.dev/weather?{params}"
        with urlopen(url, timeout=self._timeout_seconds) as response:  # noqa: S310
            data = json.load(response)

        weather_entries = data.get("weather", [])
        if not weather_entries:
            return []

        if resolution not in {"hourly", "daily"}:
            raise ValueError("resolution muss hourly oder daily sein")

        points: list[WeatherSeriesPoint] = []
        if resolution == "hourly":
            for entry in weather_entries:
                if entry.get("timestamp") and entry.get("temperature") is not None:
                    points.append(
                        WeatherSeriesPoint(
                            timestamp=entry["timestamp"],
                            temperature_c=float(entry.get("temperature", 0.0)),
                            cloud_cover_percent=float(entry.get("cloud_cover") or 0.0),
                        )
                    )
        else:
            buckets: dict[str, list[dict]] = {}
            for entry in weather_entries:
                timestamp = entry.get("timestamp")
                if not timestamp:
                    continue
                day_key = timestamp[:10]
                buckets.setdefault(day_key, []).append(entry)
            for day_key, entries in sorted(buckets.items()):
                temps = [e.get("temperature") for e in entries if e.get("temperature") is not None]
                if not temps:
                    continue
                clouds = [e.get("cloud_cover") for e in entries if e.get("cloud_cover") is not None]
                points.append(
                    WeatherSeriesPoint(
                        timestamp=day_key,
                        temperature_c=float(sum(temps) / len(temps)),
                        cloud_cover_percent=float(sum(clouds) / len(clouds)) if clouds else 0.0,
                    )
                )

        cache_file.write_text(json.dumps([p.__dict__ for p in points]), encoding="utf-8")
        return points

    def _cache_file(self, latitude: float, longitude: float, day: date, station_id: str | None) -> Path:
        station_key = station_id or "auto"
        key = f"{latitude:.4f}_{longitude:.4f}_{day.isoformat()}_{station_key}.json"
        return self._cache_dir / key
