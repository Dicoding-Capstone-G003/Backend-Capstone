from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.database import executemany, get_connection
from app.models_db import ForecastLogRecord
from app.schemas import ForecastResponse, LogRecordResponse, LogsResponse
from app.services.feature_builder import FeatureBuilder
from app.services.model_loader import RegionModelLoader
from app.services.openmeteo_client import OpenMeteoClient


logger = logging.getLogger(__name__)


class ForecastService:
    def __init__(self) -> None:
        self.model_loader = RegionModelLoader()
        self.openmeteo_client = OpenMeteoClient()
        self.feature_builder = FeatureBuilder()

    def _transform_features(self, preprocessor: Any, features: pd.DataFrame) -> Any:
        if preprocessor is None:
            return features

        candidate_features = features.copy()
        transformer = preprocessor
        if isinstance(preprocessor, dict):
            for key in ("transformer", "preprocessor", "pipeline", "scaler"):
                value = preprocessor.get(key)
                if hasattr(value, "transform"):
                    transformer = value
                    break
            else:
                transformer = None

        expected_columns = getattr(preprocessor, "feature_columns", None)
        if expected_columns is None:
            expected_columns = getattr(preprocessor, "feature_names_in_", None)
        if expected_columns is None and isinstance(preprocessor, dict):
            expected_columns = preprocessor.get("feature_columns")
        if expected_columns is not None:
            missing_columns = [column for column in expected_columns if column not in candidate_features.columns]
            for column in missing_columns:
                candidate_features[column] = 0.0
            candidate_features = candidate_features[list(expected_columns)]

        if transformer is None:
            return candidate_features

        return transformer.transform(candidate_features)

    def _predict_from_collection(self, predictors: Any, features: Any) -> Optional[List[float]]:
        if isinstance(predictors, dict):
            values: List[float] = []
            for key in sorted(predictors, key=lambda item: str(item)):
                prediction = np.asarray(predictors[key].predict(features), dtype=float).reshape(-1)
                if prediction.size == 0:
                    return None
                values.append(float(prediction[0]))
            if len(values) == 24:
                return np.maximum(np.asarray(values), 0.0).round(4).tolist()

        if isinstance(predictors, (list, tuple)):
            values = []
            for predictor in predictors:
                prediction = np.asarray(predictor.predict(features), dtype=float).reshape(-1)
                if prediction.size == 0:
                    return None
                values.append(float(prediction[0]))
            if len(values) == 24:
                return np.maximum(np.asarray(values), 0.0).round(4).tolist()

        return None

    def _predict_24_hours(
        self,
        model: Any,
        preprocessor: Any,
        future_frame: pd.DataFrame,
        single_row_frame: pd.DataFrame,
    ) -> List[float]:
        errors: List[str] = []

        for frame in (single_row_frame, future_frame):
            try:
                transformed = self._transform_features(preprocessor, frame.drop(columns=["timestamp"], errors="ignore"))
                collection_prediction = self._predict_from_collection(model, transformed)
                if collection_prediction is not None:
                    return collection_prediction

                raw_prediction = model.predict(transformed)
                predictions = np.asarray(raw_prediction, dtype=float)
                if predictions.ndim == 2 and predictions.shape[0] == 1:
                    predictions = predictions[0]
                elif predictions.ndim == 2 and predictions.shape[1] == 1:
                    predictions = predictions[:, 0]

                if predictions.size == 24:
                    return np.maximum(predictions.reshape(-1), 0.0).round(4).tolist()
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))

        raise RuntimeError(
            "Model prediction gagal untuk kedua strategi inference. "
            f"Detail: {' | '.join(errors) if errors else 'unknown error'}"
        )

    def _save_logs(
        self,
        region_name: str,
        model_version: str,
        request_time: str,
        forecast_hours: List[str],
        model_prediction: List[float],
        openmeteo_reference: List[float],
    ) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        rows = [
            ForecastLogRecord(
                region_name=region_name,
                model_version=model_version,
                request_time=request_time,
                forecast_time=forecast_hour,
                horizon_hour=index + 1,
                model_prediction=float(model_prediction[index]),
                openmeteo_reference=float(openmeteo_reference[index]),
                created_at=created_at,
            )
            for index, forecast_hour in enumerate(forecast_hours)
        ]

        executemany(
            """
            INSERT INTO forecast_logs (
                region_name,
                model_version,
                request_time,
                forecast_time,
                horizon_hour,
                model_prediction,
                openmeteo_reference,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.region_name,
                    row.model_version,
                    row.request_time,
                    row.forecast_time,
                    row.horizon_hour,
                    row.model_prediction,
                    row.openmeteo_reference,
                    row.created_at,
                )
                for row in rows
            ],
        )

    def generate_forecast(self, region_name: str) -> ForecastResponse:
        try:
            assets = self.model_loader.load_region_assets(region_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Gagal memuat artifact model: {exc}") from exc

        region = assets["region"]
        logger.info("Generating forecast for region=%s", region["display_name"])

        try:
            hourly_payload = self.openmeteo_client.fetch_forecast(
                latitude=region["latitude"],
                longitude=region["longitude"],
            )
            frames = self.feature_builder.build_inference_frames(hourly_payload)
            model_prediction = self._predict_24_hours(
                model=assets["model"],
                preprocessor=assets["preprocessor"],
                future_frame=frames["future_frame"],
                single_row_frame=frames["single_row_frame"],
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Gagal menjalankan inference: {exc}") from exc

        future_frame = frames["future_frame"]
        forecast_hours = [
            timestamp.isoformat()
            for timestamp in pd.to_datetime(future_frame["timestamp"]).dt.to_pydatetime()
        ]
        openmeteo_reference = np.maximum(
            future_frame["shortwave_radiation"].astype(float).to_numpy(),
            0.0,
        ).round(4).tolist()

        request_time = datetime.now(timezone.utc).isoformat()
        self._save_logs(
            region_name=region["display_name"],
            model_version=assets["model_version"],
            request_time=request_time,
            forecast_hours=forecast_hours,
            model_prediction=model_prediction,
            openmeteo_reference=openmeteo_reference,
        )

        return ForecastResponse(
            region_name=region["display_name"],
            model_version=assets["model_version"],
            generated_at=datetime.now(timezone.utc),
            forecast_hours=forecast_hours,
            model_prediction=model_prediction,
            openmeteo_reference=openmeteo_reference,
            source_weather="Open-Meteo forecast API",
            notes=(
                "MVP backend memakai Open-Meteo sebagai sumber weather forecast dan reference pembanding. "
                "Nilai openmeteo_reference bukan ground-truth sensor measurement."
            ),
        )

    def list_logs(self, limit: int = 200, region_name: Optional[str] = None) -> LogsResponse:
        params: List[Any] = []
        query = """
            SELECT
                id,
                region_name,
                model_version,
                request_time,
                forecast_time,
                horizon_hour,
                model_prediction,
                openmeteo_reference,
                created_at
            FROM forecast_logs
        """

        if region_name is not None:
            region_config = self.model_loader.get_region_config(region_name)
            query += " WHERE region_name = ?"
            params.append(region_config["display_name"])

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        items = [LogRecordResponse(**dict(row)) for row in rows]
        return LogsResponse(total=len(items), items=items)
