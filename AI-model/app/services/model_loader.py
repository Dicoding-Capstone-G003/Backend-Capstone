from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import joblib

from app.config import get_settings


class RegionModelLoader:
    def __init__(self) -> None:
        self.settings = get_settings()

    def normalize_region_name(self, region_name: str) -> str:
        return region_name.strip().lower().replace("_", " ")

    def get_region_config(self, region_name: str) -> Dict[str, Any]:
        region_key = self.normalize_region_name(region_name)
        region_config = self.settings.region_mapping.get(region_key)
        if region_config is None:
            raise KeyError(f"Region '{region_name}' tidak didukung.")
        return region_config

    @lru_cache(maxsize=16)
    def load_region_assets(self, region_name: str) -> Dict[str, Any]:
        region_config = self.get_region_config(region_name)
        region_dir = self.settings.model_root / region_config["folder_name"]

        model_path = region_dir / "xgboost_models.joblib"
        preprocessor_path = region_dir / "preprocessor.joblib"
        metrics_path = region_dir / "metrics.json"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model untuk region '{region_config['display_name']}' tidak ditemukan di {model_path}."
            )
        if not preprocessor_path.exists():
            raise FileNotFoundError(
                f"Preprocessor untuk region '{region_config['display_name']}' tidak ditemukan di {preprocessor_path}."
            )

        metrics: Dict[str, Any] = {}
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

        model = joblib.load(model_path)
        preprocessor = joblib.load(preprocessor_path)

        model_version = (
            str(metrics.get("model_version"))
            if metrics.get("model_version")
            else model_path.name
        )

        return {
            "region": region_config,
            "model": model,
            "preprocessor": preprocessor,
            "metrics": metrics,
            "model_version": model_version,
            "paths": {
                "model_path": str(model_path),
                "preprocessor_path": str(preprocessor_path),
                "metrics_path": str(metrics_path),
            },
        }

