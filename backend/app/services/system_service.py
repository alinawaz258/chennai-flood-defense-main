from __future__ import annotations

from backend.app.models.schemas import EmergencyUnit
from backend.app.services.bigquery_service import BigQueryRepository
from backend.app.services.clearance_service import RoadClearanceService
from backend.app.services.deployment_service import EmergencyDeploymentService
from backend.app.services.risk_engine import compute_zone_risk
from backend.app.services.routing_service import RoutingEngine


class FloodDefenseService:
    def __init__(self) -> None:
        self.repo = BigQueryRepository()
        self.routing = RoutingEngine()
        self.deployment = EmergencyDeploymentService()
        self.clearance = RoadClearanceService()

    def forecast(self):
        return self.repo.forecast_rainfall()

    def zone_risk(self, rainfall_multiplier: float = 1.0):
        forecast_df = self.forecast()
        zones_df = self.repo.fetch_zones()
        return compute_zone_risk(zones_df, forecast_df, rainfall_multiplier=rainfall_multiplier)

    def route(self, source: str, destination: str, rainfall_multiplier: float = 1.0):
        zone_df = self.zone_risk(rainfall_multiplier=rainfall_multiplier)
        graph, blocked_edges = self.routing.build_graph(zone_df)
        route = self.routing.get_safe_route(graph, source, destination)
        route["blocked_edges"] = blocked_edges
        return route, zone_df, blocked_edges

    def deploy(self, units: list[EmergencyUnit], rainfall_multiplier: float = 1.0):
        zone_df = self.zone_risk(rainfall_multiplier=rainfall_multiplier)
        return self.deployment.assign_units(units, zone_df), zone_df

    def simulate(self, rainfall_increase_pct: float, source: str | None, destination: str | None, units: list[EmergencyUnit]):
        multiplier = 1.0 + (rainfall_increase_pct / 100.0)
        zone_df = self.zone_risk(rainfall_multiplier=multiplier)
        graph, blocked_edges = self.routing.build_graph(zone_df)
        dispatch = self.deployment.assign_units(units, zone_df)
        clearance = self.clearance.prioritize(blocked_edges, zone_df)

        route = None
        if source and destination:
            route_dict = self.routing.get_safe_route(graph, source, destination)
            route_dict["blocked_edges"] = blocked_edges
            route = route_dict

        return multiplier, zone_df, blocked_edges, dispatch, route, clearance
