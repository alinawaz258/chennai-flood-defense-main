from __future__ import annotations

import numpy as np
import pandas as pd


def compute_zone_risk(zones_df: pd.DataFrame, forecast_df: pd.DataFrame, rainfall_multiplier: float = 1.0) -> pd.DataFrame:
    avg_rainfall = float(forecast_df["predicted_rainfall"].mean()) * rainfall_multiplier

    df = zones_df.copy()
    df["predicted_rainfall"] = avg_rainfall
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
