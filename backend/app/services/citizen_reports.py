from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd


class CitizenReportsService:
    """Stores crowd-sourced flood reports and derives zone risk adjustments."""

    def __init__(self) -> None:
        self._reports: List[Dict[str, object]] = []

    def store_report(self, report: Dict[str, object]) -> Dict[str, object]:
        payload = dict(report)
        payload["created_at"] = datetime.utcnow().isoformat()
        self._reports.append(payload)
        return payload

    def list_reports(self) -> List[Dict[str, object]]:
        return list(self._reports)

    def zone_risk_adjustments(self) -> Dict[str, float]:
        if not self._reports:
            return {}

        df = pd.DataFrame(self._reports)
        grouped = df.groupby("location").agg(
            avg_depth=("water_depth", "mean"),
            blocked_ratio=("road_blocked", "mean"),
        )
        grouped["risk_delta"] = (grouped["avg_depth"] / 100.0) + (grouped["blocked_ratio"] * 0.25)
        return grouped["risk_delta"].to_dict()

    def apply_adjustments(self, zone_df: pd.DataFrame) -> pd.DataFrame:
        adjusted = zone_df.copy()
        boosts = self.zone_risk_adjustments()
        if not boosts:
            return adjusted

        adjusted["flood_probability"] = adjusted.apply(
            lambda r: min(1.0, float(r["flood_probability"]) + float(boosts.get(r["zone_id"], 0.0))),
            axis=1,
        )
        adjusted["risk_level"] = pd.cut(
            adjusted["flood_probability"],
            bins=[-1, 0.25, 0.5, 0.75, 1.0],
            labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        ).astype(str)
        return adjusted
