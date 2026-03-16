from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

try:
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import LSTM, Dense
except Exception:  # optional dependency fallback
    Sequential = None
    LSTM = None
    Dense = None


FEATURES = ["rainfall", "elevation", "drainage_capacity", "population_density", "soil_moisture"]


@dataclass
class DeepFloodArtifacts:
    model: object | None
    feature_mean: np.ndarray
    feature_std: np.ndarray


class DeepFloodModelService:
    """LSTM-oriented flood model with deterministic fallback when TensorFlow is unavailable."""

    def __init__(self) -> None:
        self.artifacts = DeepFloodArtifacts(model=None, feature_mean=np.zeros(len(FEATURES)), feature_std=np.ones(len(FEATURES)))

    def train_model(self, training_df: pd.DataFrame, epochs: int = 10) -> None:
        x = training_df[FEATURES].astype(float).to_numpy()
        y = training_df["label"].astype(float).to_numpy()
        self.artifacts.feature_mean = x.mean(axis=0)
        self.artifacts.feature_std = np.clip(x.std(axis=0), 1e-6, None)
        x_scaled = (x - self.artifacts.feature_mean) / self.artifacts.feature_std

        if Sequential is None:
            # Fallback: keep no heavyweight model, predict via logistic score.
            self.artifacts.model = None
            return

        x_seq = x_scaled.reshape((x_scaled.shape[0], 1, x_scaled.shape[1]))
        model = Sequential([
            LSTM(32, activation="tanh", input_shape=(x_seq.shape[1], x_seq.shape[2])),
            Dense(16, activation="relu"),
            Dense(1, activation="sigmoid"),
        ])
        model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
        model.fit(x_seq, y, epochs=epochs, batch_size=16, verbose=0)
        self.artifacts.model = model

    def predict_zone_risk(self, zone_features: pd.DataFrame) -> pd.DataFrame:
        x = zone_features[FEATURES].astype(float).to_numpy()
        x_scaled = (x - self.artifacts.feature_mean) / self.artifacts.feature_std

        if self.artifacts.model is None:
            linear = 0.35 * x_scaled[:, 0] - 0.2 * x_scaled[:, 1] - 0.25 * x_scaled[:, 2] + 0.2 * x_scaled[:, 3] + 0.3 * x_scaled[:, 4]
            probs = 1 / (1 + np.exp(-linear))
        else:
            x_seq = x_scaled.reshape((x_scaled.shape[0], 1, x_scaled.shape[1]))
            probs = self.artifacts.model.predict(x_seq, verbose=0).flatten()

        result = zone_features[["zone_id"]].copy()
        result["flood_probability"] = probs.clip(0, 1)
        return result


def build_synthetic_training_data(rows: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    data = pd.DataFrame(
        {
            "rainfall": rng.uniform(5, 140, size=rows),
            "elevation": rng.uniform(2, 15, size=rows),
            "drainage_capacity": rng.uniform(10, 70, size=rows),
            "population_density": rng.uniform(10000, 35000, size=rows),
            "soil_moisture": rng.uniform(0.2, 0.95, size=rows),
        }
    )
    score = data["rainfall"] * 0.03 + data["soil_moisture"] * 2.0 - data["drainage_capacity"] * 0.02 - data["elevation"] * 0.04
    data["label"] = (score > score.median()).astype(float)
    return data


def row_iterable(df: pd.DataFrame) -> Iterable[dict]:
    return df.to_dict(orient="records")
