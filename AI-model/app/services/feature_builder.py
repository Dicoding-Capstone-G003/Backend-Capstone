from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from app.config import get_settings


class FeatureBuilder:
    WEATHER_COLUMNS = [
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
    TARGET_COLUMN = "shortwave_radiation"

    def __init__(self) -> None:
        self.settings = get_settings()

    def build_base_frame(self, hourly_payload: Dict[str, List[float]]) -> pd.DataFrame:
        frame = pd.DataFrame({"timestamp": pd.to_datetime(hourly_payload["time"])})
        for column in self.WEATHER_COLUMNS:
            frame[column] = hourly_payload.get(column, [])

        frame["ALLSKY_SFC_SW_DWN"] = frame["shortwave_radiation"].astype(float)
        frame["CLOUD_AMT"] = frame["cloud_cover"].astype(float)
        frame["T2M"] = frame["temperature_2m"].astype(float)
        frame["RH2M"] = frame["relative_humidity_2m"].astype(float)
        frame["PS"] = frame["surface_pressure"].astype(float)
        # Open-Meteo tidak memberi variabel clear-sky yang setara langsung dengan NASA POWER
        # pada konfigurasi ini, jadi untuk MVP kita pakai shortwave_radiation sebagai proxy stabil.
        frame["CLRSKY_SFC_SW_DWN"] = frame["shortwave_radiation"].astype(float)

        frame["hour"] = frame["timestamp"].dt.hour
        frame["day_of_week"] = frame["timestamp"].dt.dayofweek
        frame["month"] = frame["timestamp"].dt.month
        frame["sin_hour"] = np.sin(2 * np.pi * frame["hour"] / 24)
        frame["cos_hour"] = np.cos(2 * np.pi * frame["hour"] / 24)
        frame["sin_month"] = np.sin(2 * np.pi * frame["month"] / 12)
        frame["cos_month"] = np.cos(2 * np.pi * frame["month"] / 12)
        return frame

    def build_inference_frames(self, hourly_payload: Dict[str, List[float]]) -> Dict[str, pd.DataFrame]:
        full_frame = self.build_base_frame(hourly_payload)

        horizon = self.settings.forecast_horizon_hours
        history_frame = full_frame.iloc[:-horizon].copy()
        future_frame = full_frame.iloc[-horizon:].copy()

        if history_frame.empty:
            raise ValueError("History frame kosong. Tidak cukup data untuk membangun fitur inference.")

        context_row = history_frame.iloc[-1].copy()
        context_position = len(history_frame) - 1

        for lag in range(1, 25):
            context_row[f"ALLSKY_SFC_SW_DWN_lag_{lag}"] = full_frame["ALLSKY_SFC_SW_DWN"].shift(lag).iloc[
                context_position
            ]

        lag_columns = ["CLOUD_AMT", "T2M", "RH2M", "PS", "CLRSKY_SFC_SW_DWN"]
        for column in lag_columns:
            for lag in (1, 2, 3, 6, 12, 24):
                context_row[f"{column}_lag_{lag}"] = full_frame[column].shift(lag).iloc[context_position]

        history_target = history_frame["ALLSKY_SFC_SW_DWN"]
        history_cloud = history_frame["CLOUD_AMT"]
        history_clear_sky = history_frame["CLRSKY_SFC_SW_DWN"]

        context_row["ALLSKY_SFC_SW_DWN_roll_mean_3"] = history_target.tail(3).mean()
        context_row["ALLSKY_SFC_SW_DWN_roll_mean_6"] = history_target.tail(6).mean()
        context_row["ALLSKY_SFC_SW_DWN_roll_min_6"] = history_target.tail(6).min()
        context_row["ALLSKY_SFC_SW_DWN_roll_max_6"] = history_target.tail(6).max()
        context_row["ALLSKY_SFC_SW_DWN_roll_std_3"] = history_target.tail(3).std(ddof=0)
        context_row["ALLSKY_SFC_SW_DWN_roll_std_6"] = history_target.tail(6).std(ddof=0)
        context_row["CLOUD_AMT_roll_mean_3"] = history_cloud.tail(3).mean()
        context_row["CLOUD_AMT_roll_mean_6"] = history_cloud.tail(6).mean()
        context_row["CLOUD_AMT_roll_min_6"] = history_cloud.tail(6).min()
        context_row["CLOUD_AMT_roll_max_6"] = history_cloud.tail(6).max()
        context_row["CLOUD_AMT_roll_std_3"] = history_cloud.tail(3).std(ddof=0)
        context_row["CLOUD_AMT_roll_std_6"] = history_cloud.tail(6).std(ddof=0)
        context_row["CLRSKY_SFC_SW_DWN_roll_mean_3"] = history_clear_sky.tail(3).mean()
        context_row["CLRSKY_SFC_SW_DWN_roll_mean_6"] = history_clear_sky.tail(6).mean()
        context_row["CLRSKY_SFC_SW_DWN_roll_min_6"] = history_clear_sky.tail(6).min()
        context_row["CLRSKY_SFC_SW_DWN_roll_max_6"] = history_clear_sky.tail(6).max()
        context_row["CLRSKY_SFC_SW_DWN_roll_std_3"] = history_clear_sky.tail(3).std(ddof=0)
        context_row["CLRSKY_SFC_SW_DWN_roll_std_6"] = history_clear_sky.tail(6).std(ddof=0)
        context_row["ALLSKY_SFC_SW_DWN_diff_1"] = history_target.iloc[-1] - history_target.iloc[-2]
        context_row["ALLSKY_SFC_SW_DWN_diff_3"] = history_target.iloc[-1] - history_target.iloc[-4]
        context_row["CLOUD_AMT_diff_1"] = history_cloud.iloc[-1] - history_cloud.iloc[-2]
        context_row["CLOUD_AMT_diff_3"] = history_cloud.iloc[-1] - history_cloud.iloc[-4]

        latest_context = pd.DataFrame([context_row]).ffill().bfill().fillna(0.0)

        return {
            "full_frame": full_frame,
            "future_frame": future_frame.reset_index(drop=True),
            "single_row_frame": latest_context.reset_index(drop=True),
        }
