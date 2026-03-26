from __future__ import annotations

from typing import Dict, List

import httpx

from app.config import get_settings


class OpenMeteoClient:
    HOURLY_VARIABLES = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "rain",
        "showers",
        "surface_pressure",
        "cloud_cover",
        "cloud_cover_low",
        "cloud_cover_mid",
        "cloud_cover_high",
        "visibility",
        "wind_speed_10m",
        "wind_direction_10m",
        "shortwave_radiation",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_forecast(self, latitude: float, longitude: float) -> Dict[str, List[float]]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(self.HOURLY_VARIABLES),
            "past_days": 2,
            "forecast_days": 2,
            "timezone": self.settings.openmeteo_timezone,
        }

        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.get(self.settings.openmeteo_base_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Gagal mengambil data Open-Meteo: {exc}") from exc

        hourly = payload.get("hourly")
        if not hourly:
            raise RuntimeError("Response Open-Meteo tidak memiliki blok 'hourly'.")
        return hourly

