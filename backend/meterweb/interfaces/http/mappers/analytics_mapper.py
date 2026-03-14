from meterweb.application.dto import AnalyticsViewDTO
from meterweb.interfaces.http.schemas import AnalyticsResponse


def to_analytics_response(dto: AnalyticsViewDTO) -> AnalyticsResponse:
    return AnalyticsResponse(scope_id=dto.scope_id, scope=dto.scope, consumption=dto.consumption, cost=dto.cost)
