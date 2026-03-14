from meterweb.application.dto import ReadingViewDTO
from meterweb.interfaces.http.schemas import ReadingResponse


def to_reading_response(dto: ReadingViewDTO) -> ReadingResponse:
    return ReadingResponse(
        id=str(dto.id),
        meter_point_id=str(dto.meter_point_id),
        measured_at=dto.measured_at,
        value=dto.value,
        plausible=dto.plausible,
    )
