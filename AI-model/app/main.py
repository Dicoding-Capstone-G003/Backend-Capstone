from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.database import init_db
from app.routes.forecast import router as forecast_router


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(forecast_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()

