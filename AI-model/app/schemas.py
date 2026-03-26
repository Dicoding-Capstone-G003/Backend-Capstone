from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ForecastRequest(BaseModel):
    region_name: str = Field(..., description="Nama region, misalnya Jawa atau Sumatra")

    @field_validator("region_name")
    @classmethod
    def normalize_region_name(cls, value: str) -> str:
        return value.strip()


class ForecastResponse(BaseModel):
    region_name: str
    model_version: str
    generated_at: datetime
    forecast_hours: List[str]
    model_prediction: List[float]
    openmeteo_reference: List[float]
    source_weather: str
    notes: str


class RegionInfo(BaseModel):
    name: str
    folder_name: str
    latitude: float
    longitude: float


class RegionsResponse(BaseModel):
    regions: List[RegionInfo]


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str


class LogRecordResponse(BaseModel):
    id: int
    region_name: str
    model_version: Optional[str] = None
    request_time: str
    forecast_time: str
    horizon_hour: int
    model_prediction: float
    openmeteo_reference: float
    created_at: str


class LogsResponse(BaseModel):
    total: int
    items: List[LogRecordResponse]

