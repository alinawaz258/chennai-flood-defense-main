from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

import pandas as pd
import requests


class WeatherIngestionService:
    """Collects external rainfall streams and merges them with baseline forecast."""

    NASA_GPM_ENDPOINT = "https://gpm.nasa.gov/mock/precipitation"

    def fetch_nasa_gpm_data(self, zone_id: str) -> pd.DataFrame:
        # Mocked fallback aligned to expected NASA GPM cadence.
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        rows = [
            {"timestamp": (now + timedelta(hours=i)).isoformat(), "rainfall_mm": 12.0 + i * 1.5, "source": "nasa_gpm"}
            for i in range(6)
        ]
        return pd.DataFrame(rows)

    def fetch_openweather_data(self, lat: float, lon: float, api_key: str | None = None) -> pd.DataFrame:
        if not api_key:
            return pd.DataFrame([
                {"timestamp": datetime.utcnow().isoformat(), "rainfall_mm": 18.0, "source": "openweather_mock"}
            ])

        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        rain_mm = float(payload.get("rain", {}).get("1h", 0.0))
        return pd.DataFrame([
            {"timestamp": datetime.utcnow().isoformat(), "rainfall_mm": rain_mm, "source": "openweather"}
        ])

    def fetch_imd_radar_data(self, zone_id: str) -> pd.DataFrame:
        # IMD API integration placeholder (mocked by design for unavailable feeds).
        return pd.DataFrame([
            {"timestamp": datetime.utcnow().isoformat(), "rainfall_mm": 20.0, "source": "imd_mock", "zone_id": zone_id}
        ])

    def combine_rainfall_sources(self, forecast_df: pd.DataFrame, external_df: pd.DataFrame) -> pd.DataFrame:
        combined = pd.concat([forecast_df[["forecast_timestamp", "predicted_rainfall"]].rename(
            columns={"forecast_timestamp": "timestamp", "predicted_rainfall": "rainfall_mm"}
        ), external_df[["timestamp", "rainfall_mm"]]], ignore_index=True)
        combined["timestamp"] = pd.to_datetime(combined["timestamp"])
        return combined.sort_values("timestamp")

    def update_rainfall_intensity_feature(self, zone_features: pd.DataFrame, rainfall_df: pd.DataFrame) -> pd.DataFrame:
        df = zone_features.copy()
        intensity = float(rainfall_df["rainfall_mm"].tail(6).mean()) if not rainfall_df.empty else 0.0
        df["rainfall_intensity"] = intensity
        return df

    def build_multi_source_snapshot(self, zone_id: str, lat: float, lon: float, forecast_df: pd.DataFrame) -> Dict[str, float]:
        nasa_df = self.fetch_nasa_gpm_data(zone_id)
        openweather_df = self.fetch_openweather_data(lat=lat, lon=lon)
        imd_df = self.fetch_imd_radar_data(zone_id)
        external = pd.concat([nasa_df, openweather_df, imd_df], ignore_index=True)
        merged = self.combine_rainfall_sources(forecast_df, external)
        return {
            "latest_intensity_mm": float(merged["rainfall_mm"].tail(1).iloc[0]),
            "rolling_mean_mm": float(merged["rainfall_mm"].tail(6).mean()),
            "sources": float(external["source"].nunique()),
        }
