from datetime import date

import pytest

from meterweb import worker


class DummyUseCase:
    def __init__(self) -> None:
        self.calls = []

    def get_series(self, building_id, lat, lon, start, end, resolution):
        self.calls.append((building_id, lat, lon, start, end, resolution))
        return []


class DummyFactory:
    def create_weather_provider(self):
        return object()


def test_sync_weather_builds_concrete_provider_and_syncs(monkeypatch: pytest.MonkeyPatch) -> None:
    use_case = DummyUseCase()

    monkeypatch.setenv("WEATHER_BUILDING_ID", "00000000-0000-0000-0000-000000000001")
    monkeypatch.setenv("WEATHER_LAT", "52.52")
    monkeypatch.setenv("WEATHER_LON", "13.405")
    monkeypatch.setattr(worker.ProviderConfig, "from_env", classmethod(lambda cls: object()))
    monkeypatch.setattr(worker, "ProviderFactory", lambda config: DummyFactory())
    monkeypatch.setattr(worker, "JsonWeatherStationRepository", lambda _path: object())
    monkeypatch.setattr(worker, "WeatherSyncUseCase", lambda _provider, _repo: use_case)
    monkeypatch.setattr(worker, "date", type("DummyDate", (), {"today": staticmethod(lambda: date(2025, 1, 10))}))

    worker._sync_weather()

    assert [call[-1] for call in use_case.calls] == ["hourly", "daily"]
    assert use_case.calls[0][3] == date(2025, 1, 8)
    assert use_case.calls[0][4] == date(2025, 1, 10)
