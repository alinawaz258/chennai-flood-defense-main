from __future__ import annotations

from typing import List

import pandas as pd

from backend.app.models.schemas import ClearanceResult


class RoadClearanceService:
    def prioritize(self, blocked_edges: List[List[str]], zone_risk_df: pd.DataFrame) -> List[ClearanceResult]:
        zone_map = zone_risk_df.set_index("zone_id").to_dict("index")
        rows = []

        for idx, (source, target) in enumerate(blocked_edges, start=1):
            source_data = zone_map.get(source)
            target_data = zone_map.get(target)
            if not source_data or not target_data:
                continue

            water_depth_cm = max(source_data["estimated_water_depth"], target_data["estimated_water_depth"])
            road_area = 3500 + (idx * 400)
            depth_m = water_depth_cm / 100
            volume = road_area * depth_m
            pump_capacity = 320 + (idx * 15)
            clearance_time = volume / pump_capacity
            pop_density = max(source_data["population_density"], target_data["population_density"])
            road_importance = max(source_data["road_importance_score"], target_data["road_importance_score"])
            hospital_proximity = 1.0 + (idx % 4)
            priority_score = pop_density * road_importance * (1 / hospital_proximity)

            rows.append(
                ClearanceResult(
                    road_id=f"R-{idx:03d}",
                    zone_id=f"{source}-{target}",
                    water_depth_cm=round(float(water_depth_cm), 2),
                    clearance_time_hours=round(float(clearance_time), 2),
                    priority_score=round(float(priority_score), 2),
                )
            )

        return sorted(rows, key=lambda item: item.priority_score, reverse=True)[:5]
