import json
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from meterweb.application.errors import UpstreamServiceError
from meterweb.application.ports import WeatherProvider, WeatherSeriesPoint, WeatherSnapshot


_ALLOWED_RESOLUTIONS = {"hourly", "daily"}


class BrightSkyWeatherProvider(WeatherProvider):
    def __init__(self, cache_dir: Path, timeout_seconds: float = 5.0, base_url: str = "https://api.brightsky.dev") -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._timeout_seconds = timeout_seconds
        self._base_url = base_url.rstrip("/")

    def find_station(self, latitude: float, longitude: float) -> str:
        key = f"station_{latitude:.4f}_{longitude:.4f}.json"
        cache_file = self._cache_dir / key
        cached_station = self._read_cache(cache_file)
        if cached_station and cached_station.get("station_id"):
            return str(cached_station["station_id"])

        params = urlencode({"lat": latitude, "lon": longitude})
        url = f"{self._base_url}/sources?{params}"
        try:
            with urlopen(url, timeout=self._timeout_seconds) as response:  # noqa: S310
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise UpstreamServiceError("Bright Sky Stationssuche fehlgeschlagen.") from exc

        sources = data.get("sources", []) if isinstance(data, dict) else []
        if not sources:
            raise ValueError("Keine passende Wetterstation von Bright Sky gefunden.")
        station_id = next((source.get("id") for source in sources if source.get("id")), None)
        if not station_id:
            raise ValueError("Ungültige Bright Sky Stationsantwort.")

        station_id_str = str(station_id)
        self._write_cache(cache_file, {"station_id": station_id_str})
        return station_id_str

    def get_daily_snapshot(self, latitude: float, longitude: float, day: date, station_id: str | None = None) -> WeatherSnapshot:
        cache_file = self._cache_file(latitude, longitude, day, station_id)
        payload = self._read_cache(cache_file)
        if payload:
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
        url = f"{self._base_url}/weather?{params}"
        try:
            with urlopen(url, timeout=self._timeout_seconds) as response:  # noqa: S310
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise UpstreamServiceError("Bright Sky Wetterabruf fehlgeschlagen.") from exc

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
        self._write_cache(cache_file, cache_payload)
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
        self._validate_series_input(latitude, longitude, start_date, end_date, resolution)
        cache_file = self._cache_dir / f"series_{latitude:.4f}_{longitude:.4f}_{start_date.isoformat()}_{end_date.isoformat()}_{resolution}_{station_id or 'auto'}.json"
        cached = self._read_cache(cache_file)
        if cached:
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
        url = f"{self._base_url}/weather?{params}"
        try:
            with urlopen(url, timeout=self._timeout_seconds) as response:  # noqa: S310
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise UpstreamServiceError("Bright Sky Wetterserienabruf fehlgeschlagen.") from exc

        weather_entries = data.get("weather", [])
        if not weather_entries:
            return []

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

        self._write_cache(cache_file, [p.__dict__ for p in points])
        return points


    def _validate_series_input(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        resolution: str,
    ) -> None:
        if not -90 <= latitude <= 90:
            raise ValueError("lat muss zwischen -90 und 90 liegen")
        if not -180 <= longitude <= 180:
            raise ValueError("lon muss zwischen -180 und 180 liegen")
        if start_date > end_date:
            raise ValueError("start_date muss <= end_date sein")
        if resolution not in _ALLOWED_RESOLUTIONS:
            raise ValueError("resolution muss hourly oder daily sein")

    def _cache_file(self, latitude: float, longitude: float, day: date, station_id: str | None) -> Path:
        station_key = station_id or "auto"
        key = f"{latitude:.4f}_{longitude:.4f}_{day.isoformat()}_{station_key}.json"
        return self._cache_dir / key

    def _read_cache(self, cache_file: Path) -> dict | list | None:
        if not cache_file.exists():
            return None
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _write_cache(self, cache_file: Path, payload: dict | list) -> None:
        try:
            cache_file.write_text(json.dumps(payload), encoding="utf-8")
        except OSError:
            return
