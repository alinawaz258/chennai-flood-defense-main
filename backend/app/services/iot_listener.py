from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List

import pandas as pd

from backend.app.models.sensor_schema import SensorUpdate
from backend.app.services.bigquery_service import BigQueryRepository
from backend.app.services.risk_engine import compute_zone_risk


@dataclass
class SensorEnvelope:
    sensor_id: str
    sensor_type: str
    zone_id: str
    value: float
    unit: str
    timestamp: str
    latitude: float | None = None
    longitude: float | None = None


class IoTListenerService:
    """Ingests sensor updates from API/MQTT and refreshes flood-risk state."""

    def __init__(self, repo: BigQueryRepository | None = None) -> None:
        self.repo = repo or BigQueryRepository()
        self._buffer: List[dict] = []

    def ingest_sensor_updates(self, updates: List[SensorUpdate]) -> int:
        rows = [
            asdict(
                SensorEnvelope(
                    sensor_id=u.sensor_id,
                    sensor_type=u.sensor_type,
                    zone_id=u.zone_id,
                    value=u.value,
                    unit=u.unit,
                    timestamp=u.timestamp.isoformat(),
                    latitude=u.latitude,
                    longitude=u.longitude,
                )
            )
            for u in updates
        ]
        ingested = self.repo.insert_sensor_rows(rows)
        if ingested == 0:
            self._buffer.extend(rows)
            ingested = len(rows)
        return ingested

    def recalculate_risk(self) -> pd.DataFrame:
        zones_df = self.repo.fetch_zones()
        forecast_df = self.repo.forecast_rainfall()
        adjusted = self._apply_sensor_intensity_adjustment(zones_df)
        return compute_zone_risk(adjusted, forecast_df)

    def _apply_sensor_intensity_adjustment(self, zones_df: pd.DataFrame) -> pd.DataFrame:
        if not self._buffer:
            return zones_df

        df = zones_df.copy()
        sensor_df = pd.DataFrame(self._buffer)
        rain = sensor_df[sensor_df["sensor_type"].isin(["rain_gauge", "river_level", "water_level"])]
        if rain.empty:
            return df

        grouped = rain.groupby("zone_id")["value"].mean().to_dict()
        for zone, avg_value in grouped.items():
            mask = df["zone_id"] == zone
            if mask.any():
                # Reduced effective drainage when field intensity rises.
                df.loc[mask, "drainage_capacity"] = (
                    df.loc[mask, "drainage_capacity"] - float(avg_value) * 0.05
                ).clip(lower=5.0)
        return df

    @staticmethod
    def pipeline_description() -> str:
        return "Sensors -> MQTT/IoT Core -> Pub/Sub -> BigQuery -> Risk Engine"

    @staticmethod
    def now() -> str:
        return datetime.utcnow().isoformat()
