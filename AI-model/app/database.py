from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterable

from app.config import get_settings


def init_db() -> None:
    settings = get_settings()
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(settings.sqlite_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS forecast_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_name TEXT NOT NULL,
                model_version TEXT,
                request_time TEXT NOT NULL,
                forecast_time TEXT NOT NULL,
                horizon_hour INTEGER NOT NULL,
                model_prediction REAL NOT NULL,
                openmeteo_reference REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_forecast_logs_region_time
            ON forecast_logs(region_name, request_time)
            """
        )
        connection.commit()


@contextmanager
def get_connection():
    settings = get_settings()
    connection = sqlite3.connect(settings.sqlite_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def executemany(query: str, rows: Iterable[tuple]) -> None:
    with get_connection() as connection:
        connection.executemany(query, rows)
        connection.commit()

