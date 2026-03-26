from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.schemas import (
    ForecastRequest,
    ForecastResponse,
    HealthResponse,
    LogsResponse,
    RegionInfo,
    RegionsResponse,
)
from app.services.forecast_service import ForecastService


router = APIRouter()
settings = get_settings()
forecast_service = ForecastService()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/regions", response_model=RegionsResponse)
def get_regions() -> RegionsResponse:
    regions = [
        RegionInfo(
            name=region["display_name"],
            folder_name=region["folder_name"],
            latitude=region["latitude"],
            longitude=region["longitude"],
        )
        for region in settings.region_mapping.values()
    ]
    return RegionsResponse(regions=regions)


@router.post("/forecast", response_model=ForecastResponse)
def create_forecast(payload: ForecastRequest) -> ForecastResponse:
    return forecast_service.generate_forecast(payload.region_name)


@router.get("/logs", response_model=LogsResponse)
def get_logs(limit: int = Query(default=200, ge=1, le=1000)) -> LogsResponse:
    return forecast_service.list_logs(limit=limit)


@router.get("/logs/{region_name}", response_model=LogsResponse)
def get_logs_by_region(
    region_name: str, limit: int = Query(default=200, ge=1, le=1000)
) -> LogsResponse:
    try:
        return forecast_service.list_logs(region_name=region_name, limit=limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

