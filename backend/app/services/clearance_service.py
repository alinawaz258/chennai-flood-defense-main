from __future__ import annotations

from typing import Dict, List

import pandas as pd

from backend.app.models.schemas import ClearanceResult


class RoadClearanceService:
    """Prioritize road clearance actions based on impact and operational effort."""

    def prioritize(self, blocked_edges: List[List[str]], zone_risk_df: pd.DataFrame) -> List[ClearanceResult]:
        """Return top-5 blocked roads ranked by priority score."""
        zone_map: Dict[str, Dict[str, float]] = zone_risk_df.set_index("zone_id").to_dict("index")
        rows: List[ClearanceResult] = []

        for idx, (source, target) in enumerate(blocked_edges, start=1):
            source_data = zone_map.get(source)
            target_data = zone_map.get(target)
            if not source_data or not target_data:
                continue

            water_depth_cm = max(float(source_data["estimated_water_depth"]), float(target_data["estimated_water_depth"]))
            depth_m = water_depth_cm / 100.0

            # Simple synthetic road geometry until real GIS assets are integrated.
            road_length_m = 900.0 + (idx * 120.0)
            road_width_m = 8.0 + (idx % 3)
            volume_m3 = road_length_m * road_width_m * depth_m

            pump_capacity_m3_per_hour = 320.0 + (idx * 25.0)
            clearance_time_hours = volume_m3 / max(pump_capacity_m3_per_hour, 1.0)

            population_density = max(float(source_data["population_density"]), float(target_data["population_density"]))
            road_importance = max(float(source_data["road_importance_score"]), float(target_data["road_importance_score"]))
            priority_score = population_density * road_importance

            rows.append(
                ClearanceResult(
                    road_id=f"R-{idx:03d}",
                    zone_id=f"{source}-{target}",
                    water_depth_cm=round(water_depth_cm, 2),
                    clearance_time_hours=round(clearance_time_hours, 2),
                    priority_score=round(priority_score, 2),
                )
            )

        return sorted(rows, key=lambda item: item.priority_score, reverse=True)[:5]
