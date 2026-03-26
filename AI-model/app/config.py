from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings:
    app_name: str = os.getenv("APP_NAME", "Solar Irradiance Forecast API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "development")

    model_root: Path = Path(os.getenv("MODEL_ROOT", str(BASE_DIR))).resolve()
    data_dir: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
    sqlite_path: Path = Path(
        os.getenv("SQLITE_PATH", str((BASE_DIR / "data" / "forecast_logs.db").resolve()))
    ).resolve()

    openmeteo_base_url: str = os.getenv(
        "OPENMETEO_BASE_URL", "https://api.open-meteo.com/v1/forecast"
    )
    forecast_horizon_hours: int = int(os.getenv("FORECAST_HORIZON_HOURS", "24"))
    history_hours: int = int(os.getenv("HISTORY_HOURS", "48"))
    openmeteo_timezone: str = os.getenv("OPENMETEO_TIMEZONE", "Asia/Jakarta")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

    region_mapping: Dict[str, Dict[str, object]] = {
        "sumatra": {
            "display_name": "Sumatra",
            "folder_name": "Sumatra",
            "latitude": 0.7893,
            "longitude": 113.9213,
        },
        "jawa": {
            "display_name": "Jawa",
            "folder_name": "Jawa",
            "latitude": -7.6145,
            "longitude": 110.7122,
        },
        "kalimantan": {
            "display_name": "Kalimantan",
            "folder_name": "Kalimantan",
            "latitude": -0.2788,
            "longitude": 113.9213,
        },
        "sulawesi": {
            "display_name": "Sulawesi",
            "folder_name": "Sulawesi",
            "latitude": -2.5489,
            "longitude": 121.4456,
        },
        "nusa tenggara": {
            "display_name": "Nusa Tenggara",
            "folder_name": "Nusa_Tenggara",
            "latitude": -8.6574,
            "longitude": 117.3616,
        },
        "maluku": {
            "display_name": "Maluku",
            "folder_name": "Maluku",
            "latitude": -3.2385,
            "longitude": 130.1453,
        },
        "papua": {
            "display_name": "Papua",
            "folder_name": "Papua",
            "latitude": -4.2699,
            "longitude": 138.0804,
        },
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings

