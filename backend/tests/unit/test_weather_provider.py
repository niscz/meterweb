import io
import json
from datetime import date
from urllib.error import URLError

import pytest

from meterweb.application.errors import UpstreamServiceError
from meterweb.infrastructure.providers.weather import BrightSkyWeatherProvider


def _fake_urlopen_factory(payload: dict):
    def _fake_urlopen(_url: str, timeout: float):
        del timeout
        return io.StringIO(json.dumps(payload))

    return _fake_urlopen


def test_weather_provider_serializes_date_as_iso_in_cache(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = BrightSkyWeatherProvider(cache_dir=tmp_path)
    day = date(2025, 1, 15)

    monkeypatch.setattr(
        "meterweb.infrastructure.providers.weather.urlopen",
        _fake_urlopen_factory({"weather": [{"temperature": 10.0, "cloud_cover": 25.0}]}),
    )

    snapshot = provider.get_daily_snapshot(52.52, 13.405, day)

    assert snapshot.date == day
    cache_file = tmp_path / "52.5200_13.4050_2025-01-15_auto.json"
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    assert payload["date"] == "2025-01-15"


def test_weather_provider_raises_for_empty_temperature_samples(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = BrightSkyWeatherProvider(cache_dir=tmp_path)
    day = date(2025, 2, 3)

    monkeypatch.setattr(
        "meterweb.infrastructure.providers.weather.urlopen",
        _fake_urlopen_factory(
            {
                "weather": [
                    {"temperature": None, "cloud_cover": 10.0},
                    {"temperature": None, "cloud_cover": 20.0},
                ]
            }
        ),
    )

    with pytest.raises(ValueError, match="Keine Temperaturdaten"):
        provider.get_daily_snapshot(48.137, 11.575, day)

    cache_file = tmp_path / "48.1370_11.5750_2025-02-03_auto.json"
    assert not cache_file.exists()


def test_weather_provider_series_daily_and_hourly(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = BrightSkyWeatherProvider(cache_dir=tmp_path)
    monkeypatch.setattr(
        "meterweb.infrastructure.providers.weather.urlopen",
        _fake_urlopen_factory(
            {
                "weather": [
                    {"timestamp": "2025-01-01T00:00:00+00:00", "temperature": 3.0, "cloud_cover": 10.0},
                    {"timestamp": "2025-01-01T01:00:00+00:00", "temperature": 5.0, "cloud_cover": 30.0},
                ]
            }
        ),
    )
    hourly = provider.get_series(52.52, 13.405, date(2025, 1, 1), date(2025, 1, 1), "hourly")
    daily = provider.get_series(52.52, 13.405, date(2025, 1, 1), date(2025, 1, 1), "daily")
    assert len(hourly) == 2
    assert len(daily) == 1
    assert daily[0].temperature_c == 4.0


def test_find_station_uses_api_and_caches_result(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = BrightSkyWeatherProvider(cache_dir=tmp_path)
    call_count = 0

    def _fake_urlopen(url: str, timeout: float):
        nonlocal call_count
        call_count += 1
        assert "sources" in url
        assert "lat=52.52" in url
        assert "lon=13.405" in url
        del timeout
        return io.StringIO(json.dumps({"sources": [{"id": 12345}]}))

    monkeypatch.setattr("meterweb.infrastructure.providers.weather.urlopen", _fake_urlopen)

    station_first = provider.find_station(52.52, 13.405)
    station_second = provider.find_station(52.52, 13.405)

    assert station_first == "12345"
    assert station_second == "12345"
    assert call_count == 1


def test_weather_provider_uses_custom_base_url_for_weather_and_sources(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = BrightSkyWeatherProvider(cache_dir=tmp_path, base_url="https://example.weather")
    urls: list[str] = []

    def _fake_urlopen(url: str, timeout: float):
        urls.append(url)
        del timeout
        if "sources" in url:
            return io.StringIO(json.dumps({"sources": [{"id": "A1"}]}))
        return io.StringIO(json.dumps({"weather": [{"temperature": 10.0, "cloud_cover": 50.0}]}))

    monkeypatch.setattr("meterweb.infrastructure.providers.weather.urlopen", _fake_urlopen)

    station = provider.find_station(52.52, 13.405)
    snapshot = provider.get_daily_snapshot(52.52, 13.405, date(2025, 1, 2), station_id=station)

    assert station == "A1"
    assert snapshot.temperature_c == 10.0
    assert urls[0].startswith("https://example.weather/sources?")
    assert urls[1].startswith("https://example.weather/weather?")


def test_get_series_cache_miss_then_hit(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = BrightSkyWeatherProvider(cache_dir=tmp_path)
    calls = 0

    def _fake_urlopen(_url: str, timeout: float):
        nonlocal calls
        calls += 1
        del timeout
        return io.StringIO(
            json.dumps(
                {
                    "weather": [
                        {"timestamp": "2025-01-01T00:00:00+00:00", "temperature": 1.0, "cloud_cover": 10.0},
                    ]
                }
            )
        )

    monkeypatch.setattr("meterweb.infrastructure.providers.weather.urlopen", _fake_urlopen)

    first = provider.get_series(52.52, 13.405, date(2025, 1, 1), date(2025, 1, 1), "hourly")
    second = provider.get_series(52.52, 13.405, date(2025, 1, 1), date(2025, 1, 1), "hourly")

    assert len(first) == 1
    assert len(second) == 1
    assert calls == 1


def test_find_station_raises_upstream_service_error_on_network_error(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = BrightSkyWeatherProvider(cache_dir=tmp_path)

    def _failing_urlopen(_url: str, timeout: float):
        del timeout
        raise URLError("boom")

    monkeypatch.setattr("meterweb.infrastructure.providers.weather.urlopen", _failing_urlopen)

    with pytest.raises(UpstreamServiceError, match="Stationssuche fehlgeschlagen"):
        provider.find_station(48.1, 11.5)
