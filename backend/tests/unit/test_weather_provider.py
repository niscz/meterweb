import io
import json
from datetime import date

import pytest

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
