from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class BuildingCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class UnitCreateRequest(BaseModel):
    building_id: str
    name: str = Field(min_length=1, max_length=255)


class MeterPointCreateRequest(BaseModel):
    unit_id: str
    name: str = Field(min_length=1, max_length=255)


class ReadingCreateRequest(BaseModel):
    meter_point_id: str
    measured_at: datetime
    value: Decimal


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
    meter_point_id: str
    measured_at: datetime
    value: Decimal
    plausible: bool


class AnalyticsResponse(BaseModel):
    meter_point_id: str
    consumption: Decimal
    cost: Decimal
