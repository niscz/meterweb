from meterweb.application.dto import AnalyticsViewDTO
from meterweb.interfaces.http.schemas import AnalyticsResponse


def to_analytics_response(dto: AnalyticsViewDTO) -> AnalyticsResponse:
    return AnalyticsResponse(meter_point_id=dto.meter_point_id, consumption=dto.consumption, cost=dto.cost)
