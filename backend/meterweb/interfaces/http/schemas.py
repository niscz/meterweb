from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class BuildingCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class UnitCreateRequest(BaseModel):
    building_id: UUID
    name: str = Field(min_length=1, max_length=255)


class MeterPointCreateRequest(BaseModel):
    unit_id: UUID
    name: str = Field(min_length=1, max_length=255)


class ReadingCreateRequest(BaseModel):
    meter_register_id: UUID
    measured_at: datetime
    value: Decimal = Field(gt=Decimal("0"))


class OCRRunRequest(BaseModel):
    image_path: str = Field(min_length=1)


class PhotoReadingCreateRequest(BaseModel):
    meter_register_id: UUID
    measured_at: datetime
    image_path: str = Field(min_length=1)
    confirmed_value: Decimal | None = Field(default=None, gt=Decimal("0"))


class WeatherStationSelectRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class WeatherStationManualRequest(BaseModel):
    station_id: str = Field(min_length=1)


class WeatherSeriesRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    start_date: date
    end_date: date
    resolution: str = Field(default="daily", min_length=1)


class WeatherSyncRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    resolutions: list[str] = Field(default_factory=lambda: ["hourly", "daily"], min_length=1)


class AnalyticsComputeAbsoluteRequest(BaseModel):
    previous_value: Decimal
    current_value: Decimal
    rollover_limit: Decimal | None = None


class AnalyticsComputePulseRequest(BaseModel):
    pulse_delta: int = Field(ge=0)
    pulse_factor: Decimal = Field(gt=Decimal("0"))


class AnalyticsIntervalSampleRequest(BaseModel):
    start_at: datetime
    end_at: datetime
    value: Decimal


class AnalyticsComputeIntervalRequest(BaseModel):
    meter_register_id: UUID
    period_start: datetime
    period_end: datetime
    interval_values: list[AnalyticsIntervalSampleRequest] = Field(min_length=1)


class ReportExportRequest(BaseModel):
    meter_register_id: UUID | None = None
    meter_point_id: UUID | None = None
    building_id: UUID | None = None


class OCRCandidateResponse(BaseModel):
    value: Decimal
    confidence: float


class OCRRunResponse(BaseModel):
    text: str
    candidates: list[OCRCandidateResponse]
    best_candidate: OCRCandidateResponse | None


class PhotoReadingResponse(BaseModel):
    reading: "ReadingResponse"
    ocr_result: OCRRunResponse
    plausibility_warning: str | None


class WeatherStationResponse(BaseModel):
    station_id: str


class WeatherSyncResponse(BaseModel):
    status: str
    synced_resolutions: list[str]


class JobStatusResponse(BaseModel):
    status: str


class BuildingResponse(BaseModel):
    id: str
    name: str


class UnitResponse(BaseModel):
    id: str
    building_id: str
    name: str


class MeterPointResponse(BaseModel):
    id: str
    unit_id: str
    name: str


class ReadingResponse(BaseModel):
    id: str
    meter_register_id: str
    measured_at: datetime
    value: Decimal
    plausible: bool


class AnalyticsResponse(BaseModel):
    scope_id: UUID
    scope: str
    consumption: Decimal
    cost: Decimal


class ConsumptionResponse(BaseModel):
    consumption: Decimal
