from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from meterweb.application.use_cases.analytics import AnalyticsUseCase
from meterweb.application.use_cases.readings import (
    ProcessAbsoluteReadingUseCase,
    ProcessIntervalReadingUseCase,
    ProcessPulseReadingUseCase,
)
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_analytics_use_case
from meterweb.interfaces.http.mappers import to_analytics_response
from meterweb.interfaces.http.schemas import (
    AnalyticsComputeAbsoluteRequest,
    AnalyticsComputeIntervalRequest,
    AnalyticsComputePulseRequest,
    AnalyticsResponse,
    ConsumptionResponse,
)

router = APIRouter(tags=["v1-analytics"])


@router.get("/analytics/{meter_point_id}", response_model=AnalyticsResponse)
def analytics(request: Request, meter_point_id: UUID, price_per_unit: Decimal = Decimal("0.35"), use_case: AnalyticsUseCase = Depends(get_analytics_use_case)):
    require_auth(request)
    return to_analytics_response(use_case.execute(meter_point_id, price_per_unit))


@router.post("/analytics/compute/absolute", response_model=ConsumptionResponse)
def compute_absolute(request: Request, payload: AnalyticsComputeAbsoluteRequest):
    require_auth(request)
    consumption = ProcessAbsoluteReadingUseCase().compute_consumption(
        previous_value=payload.previous_value,
        current_value=payload.current_value,
        rollover_limit=payload.rollover_limit,
    )
    return {"consumption": consumption}


@router.post("/analytics/compute/pulse", response_model=ConsumptionResponse)
def compute_pulse(request: Request, payload: AnalyticsComputePulseRequest):
    require_auth(request)
    consumption = ProcessPulseReadingUseCase().compute_consumption(
        pulse_delta=payload.pulse_delta,
        pulse_factor=payload.pulse_factor,
    )
    return {"consumption": consumption}


@router.post("/analytics/compute/interval", response_model=ConsumptionResponse)
def compute_interval(request: Request, payload: AnalyticsComputeIntervalRequest):
    require_auth(request)
    consumption = ProcessIntervalReadingUseCase().compute_consumption(
        meter_register_id=payload.meter_register_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        interval_values=[(item.start_at, item.end_at, item.value) for item in payload.interval_values],
    )
    return {"consumption": consumption}
