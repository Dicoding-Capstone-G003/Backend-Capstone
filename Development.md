# Development Guide

Panduan singkat untuk menjalankan dan mengembangkan backend inference di project ini.

## 1. Lokasi Backend

Seluruh backend inference berada di folder:

```text
AI-model/
```

## 2. Requirement Utama

- Python
- FastAPI
- SQLite
- Artifact model per region di folder `AI-model/<Region>/`

Contoh artifact region:

```text
AI-model/Jawa/
|-- xgboost_models.joblib
|-- preprocessor.joblib
`-- metrics.json
```

## 3. Install Dependency

Masuk ke folder backend:

```bash
cd AI-model
```

Install dependency:

```bash
pip install -r requirements.txt
```

Catatan:
- Untuk development lokal, Python 3.11 atau 3.12 lebih direkomendasikan agar ekosistem `xgboost` dan `scikit-learn` lebih stabil.
- SQLite tidak butuh service tambahan karena memakai file database lokal.

## 4. Menjalankan Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## 5. Struktur Backend

```text
AI-model/app/
|-- main.py
|-- config.py
|-- schemas.py
|-- database.py
|-- models_db.py
|-- routes/
|   `-- forecast.py
`-- services/
    |-- model_loader.py
    |-- openmeteo_client.py
    |-- feature_builder.py
    `-- forecast_service.py
```

## 6. Tanggung Jawab File

- `app/main.py`
  Bootstrap FastAPI dan startup database.
- `app/config.py`
  Konfigurasi aplikasi, path model, SQLite path, dan mapping region.
- `app/schemas.py`
  Pydantic schema untuk request dan response API.
- `app/database.py`
  Inisialisasi dan helper SQLite.
- `app/routes/forecast.py`
  Endpoint API.
- `app/services/model_loader.py`
  Load artifact model per region.
- `app/services/openmeteo_client.py`
  Wrapper request ke Open-Meteo.
- `app/services/feature_builder.py`
  Bangun fitur inference dari data Open-Meteo.
- `app/services/forecast_service.py`
  Orkestrasi inference, response building, dan SQLite logging.

## 7. Alur Development

1. Tambahkan atau update artifact model di folder region.
2. Pastikan nama region ada di mapping `app/config.py`.
3. Jalankan backend.
4. Test endpoint `POST /forecast`.
5. Cek hasil logging di SQLite lewat endpoint `GET /logs`.

## 8. Catatan Implementasi MVP

- Backend tidak melakukan retraining model.
- Backend mengandalkan artifact `.joblib` yang sudah disiapkan manual.
- Open-Meteo dipakai sebagai sumber weather forecast dan reference pembanding.
- `openmeteo_reference` bukan actual sensor measurement.
- Feature builder memakai kompromi MVP untuk konteks historis minimum agar inference tetap stabil.

## 9. Next Improvement

- Tambahkan test otomatis untuk semua region.
- Tambahkan validasi artifact per region saat startup.
- Tambahkan endpoint detail per request batch jika nanti dibutuhkan frontend atau evaluasi model.
- Tambahkan dockerization bila deployment sudah siap.
