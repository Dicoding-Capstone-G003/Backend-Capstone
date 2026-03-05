from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import pandas as pd

CITIES_PATH = "data/cities.csv"
STATS_PATH = "data/city_summary.csv"

cities_df: pd.DataFrame | None = None
stats_df: pd.DataFrame | None = None


def load_cities(path: str) -> pd.DataFrame:

    df = pd.read_csv(path, header=None, encoding="latin1")

    df = df.iloc[:, :3].copy()
    df.columns = ["city", "lat", "lon"]

    df["city"] = df["city"].astype(str).str.strip()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    df = df.dropna(subset=["city", "lat", "lon"])

    return df


def load_stats(path: str) -> pd.DataFrame:

    df = pd.read_csv(path)

    df["city"] = df["city"].astype(str).str.strip()

    return df


@asynccontextmanager
async def lifespan(app: FastAPI):

    global cities_df
    global stats_df

    cities_df = load_cities(CITIES_PATH)
    stats_df = load_stats(STATS_PATH)

    yield


app = FastAPI(
    title="Solar PV Indonesia API",
    version="0.2",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/cities")
def get_cities():
    return cities_df.to_dict(orient="records")


@app.get("/stats")
def get_all_stats():
    return stats_df.to_dict(orient="records")


@app.get("/stats/{city}")
def get_stats_city(city: str):

    key = city.strip().lower()

    match = stats_df[stats_df["city"].str.lower() == key]

    if match.empty:
        raise HTTPException(status_code=404, detail="City not found")

    return match.iloc[0].to_dict()