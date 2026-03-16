from __future__ import annotations

import os
from pathlib import Path
from typing import List

import pandas as pd

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
except ImportError:  # optional dependency fallback
    bigquery = None
    service_account = None

from backend.app.core.config import get_settings


FORECAST_SQL = """
SELECT
  forecast_timestamp,
  forecast_value AS predicted_rainfall
FROM AI.FORECAST(
  MODEL `bigquery-public-data.ml_datasets.timesfm_model`,
  (
    SELECT
      timestamp,
      rainfall_mm
    FROM `{project_id}.{dataset_id}.{rainfall_table}`
    ORDER BY timestamp
  ),
  STRUCT(7 AS horizon, 0.8 AS confidence_level)
)
ORDER BY forecast_timestamp;
""".strip()


class BigQueryRepository:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = self._create_client()

    def _create_client(self):
        if not self.settings.project_id or bigquery is None:
            return None

        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not credentials_path:
            raise RuntimeError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set."
            )

        if not Path(credentials_path).exists():
            raise RuntimeError(
                f"Credentials file not found at: {credentials_path}"
            )

        if service_account is None:
            raise RuntimeError("google.oauth2.service_account is not installed.")

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )

        return bigquery.Client(
            credentials=credentials,
            project=credentials.project_id,
        )

    def forecast_rainfall(self) -> pd.DataFrame:
        if self.client is None:
            return self._mock_forecast()

        query = FORECAST_SQL.format(
            project_id=self.settings.project_id,
            dataset_id=self.settings.dataset_id,
            rainfall_table=self.settings.rainfall_table,
        )

        job = self.client.query(query)
        df = job.result().to_dataframe()

        return df[["forecast_timestamp", "predicted_rainfall"]]

    def fetch_zones(self) -> pd.DataFrame:
        if self.client is None:
            return self._mock_zones()

        table = f"`{self.settings.project_id}.{self.settings.dataset_id}.{self.settings.zones_table}`"

        query = f"""
        SELECT
          CAST(zone_id AS STRING) AS zone_id,
          CAST(elevation AS FLOAT64) AS elevation,
          CAST(drainage_capacity AS FLOAT64) AS drainage_capacity,
          CAST(population_density AS FLOAT64) AS population_density,
          CAST(road_importance_score AS FLOAT64) AS road_importance_score
        FROM {table}
        """

        return self.client.query(query).result().to_dataframe()

    def insert_sensor_rows(self, rows: List[dict]) -> int:
        """Insert sensor telemetry rows into BigQuery; fallback returns 0 when unavailable."""
        if not rows:
            return 0
        if self.client is None:
            return 0

        table_id = f"{self.settings.project_id}.{self.settings.dataset_id}.sensor_updates"
        errors = self.client.insert_rows_json(table_id, rows)
        if errors:
            return 0
        return len(rows)

    @staticmethod
    def _mock_forecast() -> pd.DataFrame:
        periods = pd.date_range(pd.Timestamp.utcnow().normalize(), periods=7, freq="D")
        rain = [42.0, 58.0, 71.0, 84.0, 69.0, 55.0, 48.0]

        return pd.DataFrame(
            {
                "forecast_timestamp": periods.astype(str),
                "predicted_rainfall": rain,
            }
        )

    @staticmethod
    def _mock_zones() -> pd.DataFrame:
        return pd.DataFrame(
            [
                ["T_Nagar", 6.0, 35.0, 28000.0, 0.95],
                ["Guindy", 8.0, 45.0, 21000.0, 0.80],
                ["Velachery", 4.0, 25.0, 25000.0, 0.90],
                ["Saidapet", 5.0, 30.0, 23000.0, 0.85],
                ["Adyar", 3.0, 20.0, 19000.0, 0.75],
                ["Mylapore", 4.2, 28.0, 26000.0, 0.82],
                ["Anna_Nagar", 9.5, 52.0, 24000.0, 0.88],
                ["Kodambakkam", 6.8, 34.0, 23500.0, 0.84],
                ["Perambur", 7.8, 40.0, 22000.0, 0.81],
                ["Tambaram", 11.0, 60.0, 18000.0, 0.72],
            ],
            columns=[
                "zone_id",
                "elevation",
                "drainage_capacity",
                "population_density",
                "road_importance_score",
            ],
        )


def fetch_forecast_with_pandas() -> pd.DataFrame:
    return BigQueryRepository().forecast_rainfall()


def forecast_sql_template() -> str:
    return FORECAST_SQL


def to_forecast_rows(df: pd.DataFrame) -> List[dict]:
    return [
        {
            "forecast_timestamp": str(row.forecast_timestamp),
            "predicted_rainfall": float(row.predicted_rainfall),
        }
        for row in df.itertuples(index=False)
    ]
