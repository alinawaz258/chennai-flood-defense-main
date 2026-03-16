from __future__ import annotations

from typing import Dict, List

import networkx as nx
import pandas as pd

from backend.app.services.routing_service import RoutingEngine


class EvacuationPlannerService:
    """Assigns zones to shelters and computes route/time estimates."""

    def __init__(self) -> None:
        self.routing_engine = RoutingEngine()

    def create_plan(self, zone_df: pd.DataFrame, shelters: List[Dict[str, object]]) -> List[Dict[str, object]]:
        graph, _ = self.routing_engine.build_graph(zone_df)
        shelter_capacity = {s["shelter_id"]: int(s["capacity"]) for s in shelters}
        shelter_zone = {s["shelter_id"]: str(s["zone_id"]) for s in shelters}

        plans: List[Dict[str, object]] = []
        critical = zone_df.sort_values("flood_probability", ascending=False)
        for row in critical.itertuples(index=False):
            zone = row.zone_id
            pop = int(row.population_density / 10)
            best = self._pick_shelter(graph, zone, shelter_capacity, shelter_zone)
            if not best:
                plans.append({"zone_id": zone, "shelter_id": None, "evacuation_route": [], "estimated_evacuation_time_minutes": -1})
                continue

            sid, route, dist = best
            shelter_capacity[sid] = max(0, shelter_capacity[sid] - pop)
            plans.append(
                {
                    "zone_id": zone,
                    "shelter_id": sid,
                    "evacuation_route": route,
                    "estimated_evacuation_time_minutes": round((dist / 20.0) * 60.0, 1),
                }
            )
        return plans

    @staticmethod
    def _pick_shelter(graph: nx.Graph, zone: str, capacities: Dict[str, int], shelter_zone: Dict[str, str]):
        best = None
        for sid, cap in capacities.items():
            if cap <= 0:
                continue
            s_zone = shelter_zone[sid]
            if zone not in graph or s_zone not in graph:
                continue
            try:
                route = nx.dijkstra_path(graph, source=zone, target=s_zone, weight="weight")
                dist = nx.path_weight(graph, route, weight="base_distance")
                if best is None or dist < best[2]:
                    best = (sid, route, float(dist))
            except nx.NetworkXNoPath:
                continue
        return best
