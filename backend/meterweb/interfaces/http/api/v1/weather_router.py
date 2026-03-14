from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from meterweb.application.use_cases.weather import WeatherSyncUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_weather_sync_use_case
from meterweb.interfaces.http.mappers import to_weather_series_item
from meterweb.interfaces.http.schemas import (
    WeatherSeriesRequest,
    WeatherStationManualRequest,
    WeatherStationResponse,
    WeatherStationSelectRequest,
    WeatherSyncRequest,
    WeatherSyncResponse,
)

router = APIRouter(tags=["v1-weather"])


@router.post("/weather/buildings/{building_id}/station", response_model=WeatherStationResponse)
def get_station(
    request: Request,
    building_id: UUID,
    payload: WeatherStationSelectRequest,
    use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case),
):
    require_auth(request)
    return {"station_id": use_case.select_station(building_id, payload.lat, payload.lon)}


@router.post("/weather/buildings/{building_id}/station/auto")
def set_station_auto(request: Request, building_id: UUID, use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case)):
    require_auth(request)
    use_case.set_auto_station(building_id)
    return {"status": "ok"}


@router.post("/weather/buildings/{building_id}/station/manual")
def set_station_manual(
    request: Request,
    building_id: UUID,
    payload: WeatherStationManualRequest,
    use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case),
):
    require_auth(request)
    use_case.set_manual_station(building_id, payload.station_id)
    return {"status": "ok"}


@router.get("/weather/buildings/{building_id}/series")
def weather_series(
    request: Request,
    building_id: UUID,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    resolution: str = "daily",
    use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case),
):
    require_auth(request)
    points = use_case.get_series(building_id, lat, lon, start_date, end_date, resolution)
    return [to_weather_series_item(point) for point in points]


@router.post("/weather/buildings/{building_id}/series")
def weather_series_post(
    request: Request,
    building_id: UUID,
    payload: WeatherSeriesRequest,
    use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case),
):
    require_auth(request)
    points = use_case.get_series(
        building_id,
        payload.lat,
        payload.lon,
        payload.start_date.date(),
        payload.end_date.date(),
        payload.resolution,
    )
    return [to_weather_series_item(point) for point in points]


@router.post("/weather/buildings/{building_id}/sync", response_model=WeatherSyncResponse)
def sync_weather(
    request: Request,
    building_id: UUID,
    payload: WeatherSyncRequest,
    use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case),
):
    require_auth(request)
    today = date.today()
    start = today.replace(day=1)
    for resolution in payload.resolutions:
        use_case.get_series(building_id, payload.lat, payload.lon, start, today, resolution)
    return {"status": "ok", "synced_resolutions": payload.resolutions}
