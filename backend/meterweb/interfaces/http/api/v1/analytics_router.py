from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from meterweb.application.use_cases.analytics import AnalyticsUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_analytics_use_case
from meterweb.interfaces.http.mappers import to_analytics_response
from meterweb.interfaces.http.schemas import AnalyticsResponse

router = APIRouter(tags=["v1-analytics"])


@router.get("/analytics/{meter_point_id}", response_model=AnalyticsResponse)
def analytics(request: Request, meter_point_id: UUID, price_per_unit: Decimal = Decimal("0.35"), use_case: AnalyticsUseCase = Depends(get_analytics_use_case)):
    require_auth(request)
    return to_analytics_response(use_case.execute(meter_point_id, price_per_unit))
