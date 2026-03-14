from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from meterweb.application.use_cases.weather import WeatherSyncUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_weather_sync_use_case
from meterweb.interfaces.http.mappers import to_weather_series_item

router = APIRouter(tags=["v1-weather"])


@router.get("/weather/buildings/{building_id}/station")
def get_station(request: Request, building_id: UUID, lat: float, lon: float, use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case)):
    require_auth(request)
    return {"station_id": use_case.select_station(building_id, lat, lon)}


@router.post("/weather/buildings/{building_id}/station/auto")
def set_station_auto(request: Request, building_id: UUID, use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case)):
    require_auth(request)
    use_case.set_auto_station(building_id)
    return {"status": "ok"}


@router.post("/weather/buildings/{building_id}/station/manual")
def set_station_manual(request: Request, building_id: UUID, station_id: str, use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case)):
    require_auth(request)
    use_case.set_manual_station(building_id, station_id)
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
