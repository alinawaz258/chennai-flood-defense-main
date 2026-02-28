from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from backend.app.models.schemas import DeploymentAssignment, EmergencyUnit


class EmergencyDeploymentService:
    def assign_units(self, units: List[EmergencyUnit], zone_risk_df: pd.DataFrame) -> List[DeploymentAssignment]:
        severe = zone_risk_df[zone_risk_df["risk_level"].isin(["HIGH", "CRITICAL"])].copy()
        if severe.empty or not units:
            return []

        severe = severe.sort_values("flood_probability", ascending=False).reset_index(drop=True)
        targets = severe["zone_id"].tolist()

        size = max(len(units), len(targets))
        cost_matrix = np.full((size, size), fill_value=1e6, dtype=float)

        for i, unit in enumerate(units):
            for j, zone in enumerate(targets):
                pseudo_distance = self._zone_distance(unit.current_zone, zone)
                eta_minutes = (pseudo_distance / max(unit.speed_kmph, 1.0)) * 60
                risk_boost = float(severe.loc[j, "flood_probability"]) * 10
                cost_matrix[i, j] = eta_minutes - risk_boost

        row_idx, col_idx = linear_sum_assignment(cost_matrix)
        assignments: List[DeploymentAssignment] = []

        for r, c in zip(row_idx, col_idx):
            if r >= len(units) or c >= len(targets):
                continue
            unit = units[r]
            zone = targets[c]
            eta = (self._zone_distance(unit.current_zone, zone) / max(unit.speed_kmph, 1.0)) * 60
            assignments.append(
                DeploymentAssignment(unit_id=unit.unit_id, zone_id=zone, eta_minutes=round(float(eta), 2))
            )

        return assignments

    @staticmethod
    def _zone_distance(zone_a: str, zone_b: str) -> float:
        if zone_a == zone_b:
            return 1.0
        token_distance = abs(len(zone_a) - len(zone_b)) + 3
        return float(token_distance)
