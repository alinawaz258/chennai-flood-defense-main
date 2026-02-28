from __future__ import annotations

from typing import List, Optional

import pandas as pd

from backend.app.models.schemas import EmergencyUnit
from backend.app.services.bigquery_service import BigQueryRepository
from backend.app.services.clearance_service import RoadClearanceService
from backend.app.services.deployment_service import EmergencyDeploymentService
from backend.app.services.risk_engine import compute_zone_risk
from backend.app.services.routing_service import RoutingEngine


class FloodDefenseService:
    """Facade service orchestrating forecasting, risk, routing, deployment, and simulation."""

    def __init__(self) -> None:
        self.repo = BigQueryRepository()
        self.routing = RoutingEngine()
        self.deployment = EmergencyDeploymentService()
        self.clearance = RoadClearanceService()

    def forecast(self) -> pd.DataFrame:
        """Get rainfall forecast from BigQuery or local fallback data."""
        return self.repo.forecast_rainfall()

    def zone_risk(self, rainfall_multiplier: float = 1.0) -> pd.DataFrame:
        """Compute latest zone-level flood risk metrics."""
        forecast_df = self.forecast()
        zones_df = self.repo.fetch_zones()
        return compute_zone_risk(zones_df, forecast_df, rainfall_multiplier=rainfall_multiplier)

    def route(
        self,
        source: str,
        destination: str,
        rainfall_multiplier: float = 1.0,
    ) -> tuple[dict, pd.DataFrame, List[List[str]]]:
        """Build flood-aware graph and compute safest route between zones."""
        zone_df = self.zone_risk(rainfall_multiplier=rainfall_multiplier)
        graph, blocked_edges = self.routing.build_graph(zone_df)
        route = self.routing.get_safe_route(graph, source, destination)
        route["blocked_edges"] = blocked_edges
        return route, zone_df, blocked_edges

    def deploy(self, units: List[EmergencyUnit], rainfall_multiplier: float = 1.0):
        """Assign emergency units to severe-risk zones."""
        zone_df = self.zone_risk(rainfall_multiplier=rainfall_multiplier)
        return self.deployment.assign_units(units, zone_df), zone_df

    @staticmethod
    def _compute_disaster_severity_index(zone_df: pd.DataFrame) -> float:
        """Compute composite severity index from flood probability and population density."""
        if zone_df.empty:
            return 0.0
        avg_flood_probability = float(zone_df["flood_probability"].mean())
        total_population_density = float(zone_df["population_density"].sum())
        return round(avg_flood_probability * total_population_density, 2)

    @staticmethod
    def _build_recommendations(zone_df: pd.DataFrame, blocked_edges: List[List[str]]) -> List[str]:
        """Generate response recommendations using current risk and mobility constraints."""
        recommendations: List[str] = []
        critical_count = int((zone_df["risk_level"] == "CRITICAL").sum())
        high_count = int((zone_df["risk_level"] == "HIGH").sum())

        if critical_count > 0:
            recommendations.append("Activate Level 2 emergency protocol")

        if high_count > 2:
            recommendations.append("Deploy additional pump units")

        if blocked_edges:
            recommendations.append("Restrict traffic in affected corridors")

        if not recommendations:
            recommendations.append("Maintain standard flood monitoring operations")

        return recommendations

    def simulate(
        self,
        rainfall_increase_pct: float,
        source: Optional[str],
        destination: Optional[str],
        units: List[EmergencyUnit],
    ):
        """Run an end-to-end flood simulation with adjusted rainfall inputs."""
        multiplier = 1.0 + (rainfall_increase_pct / 100.0)
        zone_df = self.zone_risk(rainfall_multiplier=multiplier)

        # Recalculate road network and routing under simulated flood conditions.
        graph, blocked_edges = self.routing.build_graph(zone_df)
        dispatch = self.deployment.assign_units(units, zone_df)
        clearance = self.clearance.prioritize(blocked_edges, zone_df)
        disaster_severity_index = self._compute_disaster_severity_index(zone_df)
        recommendations = self._build_recommendations(zone_df, blocked_edges)

        route = None
        if source and destination:
            route_dict = self.routing.get_safe_route(graph, source, destination)
            route_dict["blocked_edges"] = blocked_edges
            route = route_dict

        return (
            multiplier,
            zone_df,
            blocked_edges,
            dispatch,
            route,
            clearance,
            disaster_severity_index,
            recommendations,
        )
