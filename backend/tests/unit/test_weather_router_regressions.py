from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import meterweb.interfaces.http.api.v1.weather_router as weather_router


class _FakeWeatherSyncUseCase:
    def __init__(self) -> None:
        self.calls = []

    def select_station(self, building_id, lat, lon):
        self.calls.append(("select_station", building_id, lat, lon))
        return "station-compat"

    def get_series(self, building_id, lat, lon, start_date, end_date, resolution):
        self.calls.append(("get_series", building_id, lat, lon, start_date, end_date, resolution))
        return []


def test_get_station_get_route_handler_kept_for_backward_compatibility(monkeypatch) -> None:
    monkeypatch.setattr(weather_router, "require_auth", lambda _request: None)
    fake = _FakeWeatherSyncUseCase()

    result = weather_router.get_station(
        request=SimpleNamespace(),
        building_id=uuid4(),
        lat=48.1,
        lon=11.5,
        use_case=fake,
    )

    assert result == {"station_id": "station-compat"}
    assert fake.calls[0][0] == "select_station"


def test_weather_series_post_uses_date_payload_without_silent_truncation(monkeypatch) -> None:
    monkeypatch.setattr(weather_router, "require_auth", lambda _request: None)
    fake = _FakeWeatherSyncUseCase()
    building_id = uuid4()
    payload = SimpleNamespace(
        lat=48.1,
        lon=11.5,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        resolution="daily",
    )

    weather_router.weather_series_post(
        request=SimpleNamespace(),
        building_id=building_id,
        payload=payload,
        use_case=fake,
    )

    call = fake.calls[-1]
    assert call[0] == "get_series"
    assert call[4] == date(2025, 1, 1)
    assert call[5] == date(2025, 1, 2)
