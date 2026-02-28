from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


ZONE_RAINFALL_SENSITIVITY: Dict[str, float] = {
    "Adyar": 1.2,
    "Velachery": 1.15,
    "Saidapet": 1.05,
    "T_Nagar": 0.9,
    "Guindy": 0.85,
}


def compute_zone_risk(
    zones_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    rainfall_multiplier: float = 1.0,
) -> pd.DataFrame:
    """Compute zone-wise flood risk using forecast rainfall and infrastructure features."""
    avg_rainfall: float = float(forecast_df["predicted_rainfall"].mean()) * rainfall_multiplier

    df: pd.DataFrame = zones_df.copy()
    # Zone-specific rainfall sensitivity makes low-lying regions react more aggressively.
    df["rainfall_sensitivity_multiplier"] = (
        df["zone_id"].map(ZONE_RAINFALL_SENSITIVITY).fillna(1.0).astype(float)
    )
    df["predicted_rainfall"] = avg_rainfall * df["rainfall_sensitivity_multiplier"]
    df["drainage_capacity_inverse"] = 1.0 / df["drainage_capacity"].clip(lower=1)

    raw_score = (
        (df["predicted_rainfall"] * 0.5)
        + ((1.0 / df["elevation"].clip(lower=0.5)) * 0.2)
        + (df["drainage_capacity_inverse"] * 0.3)
    )

    min_score, max_score = float(raw_score.min()), float(raw_score.max())
    if max_score - min_score < 1e-9:
        df["flood_probability"] = 0.0
    else:
        df["flood_probability"] = (raw_score - min_score) / (max_score - min_score)

    df["risk_level"] = pd.cut(
        df["flood_probability"],
        bins=[-np.inf, 0.25, 0.5, 0.75, np.inf],
        labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
    ).astype(str)

    water_depth_mm = (df["predicted_rainfall"] - df["drainage_capacity"]).clip(lower=0.0)
    df["estimated_water_depth"] = water_depth_mm / 10.0

    return df[
        [
            "zone_id",
            "predicted_rainfall",
            "flood_probability",
            "risk_level",
            "estimated_water_depth",
            "population_density",
            "road_importance_score",
        ]
    ]
