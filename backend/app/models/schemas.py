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
    disaster_severity_index: float
    recommendations: List[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    compute_profile: str


class ZonesResponse(BaseModel):
    zones: List[ZoneRisk]


class ForecastResponse(BaseModel):
    forecast: List[ForecastPoint]
    source: str


class ErrorResponse(BaseModel):
    detail: str


class HeatmapResponse(BaseModel):
    heatmap: Dict[str, float]


class CitizenReportRequest(BaseModel):
    location: str
    water_depth: float = Field(ge=0)
    photo_url: Optional[str] = None
    road_blocked: bool = False


class CitizenReportResponse(BaseModel):
    status: str
    report: Dict[str, object]


class TrafficRerouteRequest(BaseModel):
    source: str
    destination: str
    algorithm: str = Field(default="astar", pattern="^(astar|dijkstra)$")


class TrafficRerouteResponse(BaseModel):
    algorithm: str
    route: List[str]
    total_cost: float
    blocked_edges: List[List[str]]


class ShelterInput(BaseModel):
    shelter_id: str
    zone_id: str
    capacity: int = Field(ge=0)


class EvacuationPlanRequest(BaseModel):
    shelters: List[ShelterInput]


class EvacuationPlanItem(BaseModel):
    zone_id: str
    shelter_id: Optional[str]
    evacuation_route: List[str]
    estimated_evacuation_time_minutes: float


class EvacuationPlanResponse(BaseModel):
    plans: List[EvacuationPlanItem]


class DamageEstimateRequest(BaseModel):
    flood_depth: float = Field(ge=0)
    population: int = Field(ge=0)
    infrastructure_density: float = Field(ge=0)


class DamageEstimateResponse(BaseModel):
    estimated_economic_loss_inr: float
    people_affected: int
    critical_infrastructure_impact: float


class RecommendationsRequest(BaseModel):
    current_flood_risk_map: List[Dict[str, object]]
    available_rescue_units: List[Dict[str, object]]
    road_accessibility: List[Dict[str, object]]


class RecommendationsResponse(BaseModel):
    recommendations: List[str]


class SendAlertRequest(BaseModel):
    message: str
    channels: List[str]
    recipients: List[str]


class SendAlertResponse(BaseModel):
    message: str
    channels: List[str]
    total_recipients: int
    events: List[Dict[str, object]]
