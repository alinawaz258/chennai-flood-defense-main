# Chennai Urban Flood Defense System

## Project Structure

```text
chennai-flood-defense/
├── backend/
│   ├── app/
│   │   ├── core/config.py
│   │   ├── models/schemas.py
│   │   └── services/
│   │       ├── bigquery_service.py
│   │       ├── clearance_service.py
│   │       ├── deployment_service.py
│   │       ├── risk_engine.py
│   │       ├── routing_service.py
│   │       └── system_service.py
|   ├── chennai-flood-defense-sa.json
│   ├── main.py
│   └── run_forecast.py
├── frontend/index.html
├── sql/rainfall_forecast_timesfm.sql
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies.
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables.
   ```bash
   set PROJECT_ID="chennai-flood-defense-sa"
   set DATASET_ID="chennai_flood"
   set RAINFALL_TABLE="rainfall_history"
   set ZONES_TABLE="zones"
   set GCP_CREDENTIALS_PATH="/workspaces/chennai-flood-defense-main/backend/chennai-flood-defense-sa.json"
   set COMPUTE_CPU_VENDOR="AMD"
   set COMPUTE_CPU_FAMILY="EPYC"
   set COMPUTE_OPTIMIZED="true"
   ```
3. Run backend.
   ```bash
   uvicorn backend.main:app --reload
   ```
4. Open frontend.
   ```bash
   python3 -m http.server 8080 --directory frontend
   ```
   Browse to `http://127.0.0.1:8080`.

## Local Validation

```bash
python -m compileall backend
python -m unittest backend.tests.test_services
```

## GCP Free Tier Configuration

1. Create project and enable APIs: BigQuery API, BigQuery ML, Vertex AI API.
2. Keep usage within free tier by using:
   - BigQuery sandbox/free query limits.
   - BigQuery ML pre-trained `timesfm_model` via `AI.FORECAST` (no custom training).
3. Create service account with roles:
   - BigQuery Data Viewer
   - BigQuery Job User
4. Save service account key JSON locally and set `GCP_CREDENTIALS_PATH`.
5. Create dataset and tables:
   - `chennai_flood.rainfall_history(timestamp TIMESTAMP, rainfall_mm FLOAT64)`
   - `chennai_flood.zones(zone_id STRING, elevation FLOAT64, drainage_capacity FLOAT64, population_density FLOAT64, road_importance_score FLOAT64)`

## API Endpoints

- `GET /forecast`
- `GET /` (health with compute profile, defaults to `AMD EPYC`)
- `GET /forecast/sql`
- `GET /zones`
- `POST /route`
- `POST /deploy`
- `POST /simulate`

## BigQuery SQL (TimesFM)

`sql/rainfall_forecast_timesfm.sql` contains the production query for 7-day rainfall forecasting using `AI.FORECAST`.
