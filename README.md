# Backend-Capstone

Capstone project backend untuk forecasting solar irradiance 24 jam ke depan per region di Indonesia.

Project ini berfokus pada backend inference MVP yang:
- memuat model XGBoost per region dari artifact lokal
- mengambil weather forecast dan solar radiation reference dari Open-Meteo
- menghasilkan `model_prediction` dan `openmeteo_reference`
- menyimpan log prediksi ke SQLite untuk evaluasi lanjutan

## Project Structure

```text
Backend-Capstone/
|-- AI-model/
|   |-- app/
|   |   |-- main.py
|   |   |-- config.py
|   |   |-- schemas.py
|   |   |-- database.py
|   |   |-- models_db.py
|   |   |-- routes/
|   |   `-- services/
|   |-- Jawa/
|   |-- Sumatra/
|   |-- Kalimantan/
|   |-- Sulawesi/
|   |-- Nusa_Tenggara/
|   |-- Maluku/
|   |-- Papua/
|   |-- data/
|   |-- requirements.txt
|   `-- README.md
|-- Development.md
|-- Documentation.md
`-- LICENSE
```

## Main Features

- FastAPI backend untuk inference forecasting
- Load model artifact per region dari folder lokal
- Open-Meteo integration untuk weather forecast dan reference pembanding
- SQLite logging sederhana per horizon forecast
- Endpoint siap diuji untuk frontend MVP

## Supported Regions

- Sumatra
- Jawa
- Kalimantan
- Sulawesi
- Nusa Tenggara
- Maluku
- Papua

## Main Endpoints

- `GET /health`
- `GET /regions`
- `POST /forecast`
- `GET /logs`
- `GET /logs/{region_name}`

## Quick Start

Pindah ke folder backend:

```bash
cd AI-model
```

Install dependency:

```bash
pip install -r requirements.txt
```

Jalankan server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Documentation

- Backend run guide dan setup: [Development.md](./Development.md)
- API flow dan detail implementasi: [Documentation.md](./Documentation.md)
- Dokumentasi backend folder `AI-model`: [AI-model/README.md](./AI-model/README.md)

## MVP Note

Pada MVP ini, `openmeteo_reference` digunakan sebagai pembanding forecast di UI dan bukan ground-truth sensor measurement.
