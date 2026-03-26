# Backend Documentation

Dokumentasi ringkas backend inference solar irradiance forecasting untuk MVP.

## Overview

Backend ini dibuat untuk:
- memuat model XGBoost per region
- mengambil forecast cuaca dari Open-Meteo
- menghasilkan prediksi solar irradiance 24 jam ke depan
- mengembalikan hasil model dan reference Open-Meteo ke frontend
- menyimpan log hasil forecast ke SQLite

Target prediksi model:

```text
ALLSKY_SFC_SW_DWN
```

## Supported Regions

- Sumatra
- Jawa
- Kalimantan
- Sulawesi
- Nusa Tenggara
- Maluku
- Papua

## Region Artifact Layout

Setiap region memiliki folder sendiri di dalam `AI-model/`.

Contoh:

```text
AI-model/Jawa/
|-- xgboost_models.joblib
|-- preprocessor.joblib
`-- metrics.json
```

## High-Level Flow

1. Client mengirim `POST /forecast` dengan `region_name`
2. Backend mencari folder artifact region
3. Backend mengambil koordinat region dari internal mapping
4. Backend request data hourly forecast ke Open-Meteo
5. Backend membangun fitur inference dari data forecast dan konteks historis minimum
6. Backend menjalankan model XGBoost
7. Backend clamp hasil prediksi agar non-negative
8. Backend mengembalikan:
   - `model_prediction`
   - `openmeteo_reference`
9. Backend menyimpan hasil per horizon ke SQLite

## Endpoints

### `GET /health`

Cek status backend.

Contoh response:

```json
{
  "status": "ok",
  "app_name": "Solar Irradiance Forecast API",
  "version": "0.1.0",
  "environment": "development"
}
```

### `GET /regions`

Menampilkan daftar region yang tersedia beserta representative coordinate.

### `POST /forecast`

Request body:

```json
{
  "region_name": "Jawa"
}
```

Response body:

```json
{
  "region_name": "Jawa",
  "model_version": "xgboost_models.joblib",
  "generated_at": "2026-03-26T08:57:08.663856Z",
  "forecast_hours": [
    "2026-03-27T00:00:00",
    "2026-03-27T01:00:00"
  ],
  "model_prediction": [
    0.0725,
    0.0692
  ],
  "openmeteo_reference": [
    0.0,
    0.0
  ],
  "source_weather": "Open-Meteo forecast API",
  "notes": "MVP backend memakai Open-Meteo sebagai sumber weather forecast dan reference pembanding. Nilai openmeteo_reference bukan ground-truth sensor measurement."
}
```

Catatan:
- Response asli berisi 24 timestamp.
- Response asli berisi 24 nilai `model_prediction`.
- Response asli berisi 24 nilai `openmeteo_reference`.

### `GET /logs`

Menampilkan log prediksi tersimpan dari semua region.

### `GET /logs/{region_name}`

Menampilkan log prediksi untuk region tertentu.

## SQLite Logging

Untuk MVP, backend memakai satu tabel sederhana:

```text
forecast_logs
```

Kolom minimum:

- `id`
- `region_name`
- `model_version`
- `request_time`
- `forecast_time`
- `horizon_hour`
- `model_prediction`
- `openmeteo_reference`
- `created_at`

Satu request forecast akan menyimpan 24 baris log, masing-masing untuk satu horizon jam.

## Open-Meteo Usage

Open-Meteo dipakai untuk dua kebutuhan:
- sebagai sumber weather forecast untuk membangun fitur inference
- sebagai `openmeteo_reference` untuk pembanding forecast di UI

Istilah `actual` sengaja tidak dipakai di response karena nilai ini bukan pengukuran sensor ground-truth.

## Feature Engineering Note

Model training memakai kombinasi fitur seperti:
- cuaca
- fitur waktu cyclic
- lag target `ALLSKY_SFC_SW_DWN`
- lag fitur cuaca tertentu
- rolling statistics
- diff features

Pada backend MVP ini, feature builder mengikuti struktur artifact yang tersedia dan memakai fallback praktis untuk konteks historis awal agar inference tetap berjalan stabil.

## Important Implementation Notes

- Backend fokus untuk inference, bukan retraining.
- Logic inference dipisah dari route agar kode tetap bersih.
- Jika model atau preprocessor region tidak ditemukan, backend mengembalikan error yang jelas.
- Artifact `.joblib` dibaca langsung dari folder lokal `AI-model/<Region>/`.

## Files to Know

- [README.md](./README.md)
- [Development.md](./Development.md)
- [AI-model/README.md](./AI-model/README.md)
- [AI-model/app/main.py](./AI-model/app/main.py)
- [AI-model/app/routes/forecast.py](./AI-model/app/routes/forecast.py)
- [AI-model/app/services/forecast_service.py](./AI-model/app/services/forecast_service.py)
