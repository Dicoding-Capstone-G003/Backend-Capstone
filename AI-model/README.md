# Solar Irradiance Forecast Backend

Backend FastAPI untuk inference forecasting solar irradiance 24 jam ke depan per region menggunakan artifact model XGBoost lokal.

## Struktur utama

```text
AI-model/
|-- app/
|   |-- main.py
|   |-- config.py
|   |-- schemas.py
|   |-- database.py
|   |-- models_db.py
|   |-- routes/
|   |   `-- forecast.py
|   `-- services/
|       |-- model_loader.py
|       |-- openmeteo_client.py
|       |-- feature_builder.py
|       `-- forecast_service.py
|-- Jawa/
|   |-- xgboost_models.joblib
|   |-- preprocessor.joblib
|   `-- metrics.json
|-- Sumatra/
|-- Kalimantan/
|-- Sulawesi/
|-- Nusa_Tenggara/
|-- Maluku/
|-- Papua/
|-- data/
|   `-- forecast_logs.db
|-- requirements.txt
`-- .env.example
```

## Cara jalan

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoint

- `GET /health`
- `GET /regions`
- `POST /forecast`
- `GET /logs`
- `GET /logs/{region_name}`

## Contoh request

```json
POST /forecast
{
  "region_name": "Jawa"
}
```

## Contoh response

```json
{
  "region_name": "Jawa",
  "model_version": "xgboost_models.joblib",
  "generated_at": "2026-03-26T08:30:12.100000+00:00",
  "forecast_hours": [
    "2026-03-26T09:00:00+07:00"
  ],
  "model_prediction": [
    125.42
  ],
  "openmeteo_reference": [
    132.8
  ],
  "source_weather": "Open-Meteo forecast API",
  "notes": "MVP backend memakai Open-Meteo sebagai reference pembanding forecast, bukan ground-truth sensor measurement."
}
```

Response sebenarnya akan berisi 24 timestamp, 24 nilai `model_prediction`, dan 24 nilai `openmeteo_reference`.

## Catatan MVP

- Artifact model dibaca langsung dari folder region di root `AI-model/`.
- `openmeteo_reference` dipakai sebagai pembanding forecast di UI untuk MVP, bukan actual sensor.
- SQLite menyimpan satu baris per horizon forecast agar nanti mudah dipakai untuk evaluasi dan retraining.
- Feature builder memakai fallback `ffill/bfill` untuk lag awal bila konteks historis minimum belum lengkap. Ini kompromi praktis agar inference tetap stabil.

## Related Docs

- Root overview repo: [../README.md](../README.md)
- Development guide: [../Development.md](../Development.md)
- Backend documentation: [../Documentation.md](../Documentation.md)
