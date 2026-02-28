from __future__ import annotations

from typing import Dict, List, Tuple

import networkx as nx
import pandas as pd


class RoutingEngine:
    def __init__(self) -> None:
        self.base_edges: List[Tuple[str, str, float]] = [
            ("T_Nagar", "Guindy", 7.0),
            ("T_Nagar", "Saidapet", 4.5),
            ("Saidapet", "Guindy", 3.0),
            ("Guindy", "Velachery", 6.0),
            ("Saidapet", "Velachery", 8.0),
            ("Velachery", "Adyar", 5.5),
            ("Guindy", "Adyar", 5.0),
        ]

    def build_graph(self, zone_risk_df: pd.DataFrame) -> tuple[nx.Graph, List[List[str]]]:
        risk_map = zone_risk_df.set_index("zone_id").to_dict("index")
        graph = nx.Graph()
        blocked_edges: List[List[str]] = []

        for source, target, base_distance in self.base_edges:
            src = risk_map.get(source)
            dst = risk_map.get(target)
            if not src or not dst:
                continue

            flood_probability = max(src["flood_probability"], dst["flood_probability"])
            water_depth_cm = max(src["estimated_water_depth"], dst["estimated_water_depth"])
            weight = base_distance + (flood_probability * 100) + (water_depth_cm * 50)

            if water_depth_cm > 20:
                blocked_edges.append([source, target])
                continue

            graph.add_edge(source, target, weight=weight, base_distance=base_distance)

        return graph, blocked_edges

    @staticmethod
    def _heuristic(_: str, __: str) -> float:
        return 0.0

    def get_safe_route(self, graph: nx.Graph, source: str, destination: str) -> Dict:
        if source not in graph.nodes or destination not in graph.nodes:
            return {"algorithm": "none", "route": [], "total_cost": -1}

        try:
            route = nx.astar_path(graph, source=source, target=destination, heuristic=self._heuristic, weight="weight")
            total_cost = nx.path_weight(graph, route, weight="weight")
            return {"algorithm": "astar", "route": route, "total_cost": round(total_cost, 2)}
        except nx.NetworkXNoPath:
            try:
                route = nx.dijkstra_path(graph, source=source, target=destination, weight="weight")
                total_cost = nx.path_weight(graph, route, weight="weight")
                return {"algorithm": "dijkstra", "route": route, "total_cost": round(total_cost, 2)}
            except nx.NetworkXNoPath:
                return {"algorithm": "none", "route": [], "total_cost": -1}
