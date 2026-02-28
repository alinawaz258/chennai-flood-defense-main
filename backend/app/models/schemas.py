from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    forecast_timestamp: str
    predicted_rainfall: float


class ZoneRisk(BaseModel):
    zone_id: str
    predicted_rainfall: float
    flood_probability: float
    risk_level: str
    estimated_water_depth: float


class RouteRequest(BaseModel):
    source: str
    destination: str


class RouteResponse(BaseModel):
    algorithm: str
    route: List[str]
    total_cost: float
    blocked_edges: List[List[str]]


class EmergencyUnit(BaseModel):
    unit_id: str
    current_zone: str
    speed_kmph: float = 35


class DeployRequest(BaseModel):
    units: List[EmergencyUnit]


class DeploymentAssignment(BaseModel):
    unit_id: str
    zone_id: str
    eta_minutes: float


class DeployResponse(BaseModel):
    assignments: List[DeploymentAssignment]


class ClearanceRoad(BaseModel):
    road_id: str
    zone_id: str
    road_area_m2: float
    pump_capacity_m3_per_hour: float
    hospital_proximity_km: float


class ClearanceResult(BaseModel):
    road_id: str
    zone_id: str
    water_depth_cm: float
    clearance_time_hours: float
    priority_score: float


class SimulationRequest(BaseModel):
    rainfall_increase_pct: float = Field(ge=0, le=500)
    source: Optional[str] = None
    destination: Optional[str] = None
    units: Optional[List[EmergencyUnit]] = None


class SimulationResponse(BaseModel):
    rainfall_multiplier: float
    zones: List[ZoneRisk]
    blocked_roads: List[List[str]]
    dispatch: List[DeploymentAssignment]
    route: Optional[RouteResponse] = None
    clearance_top5: List[ClearanceResult]


class HealthResponse(BaseModel):
    status: str
    service: str


class ZonesResponse(BaseModel):
    zones: List[ZoneRisk]


class ForecastResponse(BaseModel):
    forecast: List[ForecastPoint]
    source: str


class ErrorResponse(BaseModel):
    detail: str


class HeatmapResponse(BaseModel):
    heatmap: Dict[str, float]
