from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from meterweb.application.use_cases.analytics import AnalyticsUseCase
from meterweb.application.use_cases.weather import WeatherSyncUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_analytics_use_case, get_weather_sync_use_case
from meterweb.interfaces.http.schemas import JobStatusResponse, WeatherSyncRequest

router = APIRouter(tags=["v1-jobs"])


@router.post("/jobs/weather-sync/{building_id}", response_model=JobStatusResponse)
def weather_sync_job(
    request: Request,
    building_id: UUID,
    payload: WeatherSyncRequest,
    use_case: WeatherSyncUseCase = Depends(get_weather_sync_use_case),
):
    require_auth(request)
    today = date.today()
    start = today - timedelta(days=2)
    for resolution in payload.resolutions:
        use_case.get_series(building_id, payload.lat, payload.lon, start, today, resolution)
    return {"status": "ok"}


@router.post("/jobs/analytics/recompute/{meter_point_id}", response_model=JobStatusResponse)
def recompute_analytics_job(
    request: Request,
    meter_point_id: UUID,
    use_case: AnalyticsUseCase = Depends(get_analytics_use_case),
):
    require_auth(request)
    use_case.execute(meter_point_id, price_per_unit=0)
    return {"status": "ok"}
