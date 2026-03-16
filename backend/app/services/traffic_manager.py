from __future__ import annotations

from typing import Dict, List

import networkx as nx
import pandas as pd

from backend.app.services.routing_service import RoutingEngine


class TrafficManagerService:
    """Dynamic traffic management over the flood-aware road graph."""

    def __init__(self) -> None:
        self.routing_engine = RoutingEngine()

    def detect_flooded_roads(self, zone_df: pd.DataFrame) -> List[List[str]]:
        _, blocked_edges = self.routing_engine.build_graph(zone_df)
        return blocked_edges

    def dynamic_reroute(self, zone_df: pd.DataFrame, source: str, destination: str, algorithm: str = "astar") -> Dict[str, object]:
        graph, blocked = self.routing_engine.build_graph(zone_df)
        if source not in graph or destination not in graph:
            return {"algorithm": "none", "route": [], "total_cost": -1, "blocked_edges": blocked}

        try:
            if algorithm.lower() == "dijkstra":
                route = nx.dijkstra_path(graph, source=source, target=destination, weight="weight")
                algo = "dijkstra"
            else:
                route = nx.astar_path(graph, source=source, target=destination, heuristic=lambda *_: 0.0, weight="weight")
                algo = "astar"
            total_cost = nx.path_weight(graph, route, weight="weight")
            return {"algorithm": algo, "route": route, "total_cost": round(float(total_cost), 2), "blocked_edges": blocked}
        except nx.NetworkXNoPath:
            return {"algorithm": "none", "route": [], "total_cost": -1, "blocked_edges": blocked}

    def generate_evacuation_routes(self, zone_df: pd.DataFrame, origins: List[str], safe_hubs: List[str]) -> Dict[str, List[str]]:
        graph, _ = self.routing_engine.build_graph(zone_df)
        out: Dict[str, List[str]] = {}
        for origin in origins:
            for hub in safe_hubs:
                try:
                    out[origin] = nx.dijkstra_path(graph, source=origin, target=hub, weight="weight")
                    break
                except nx.NetworkXNoPath:
                    continue
            out.setdefault(origin, [])
        return out
