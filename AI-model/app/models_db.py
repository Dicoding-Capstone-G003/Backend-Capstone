from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ForecastLogRecord:
    region_name: str
    model_version: str
    request_time: str
    forecast_time: str
    horizon_hour: int
    model_prediction: float
    openmeteo_reference: float
    created_at: str

