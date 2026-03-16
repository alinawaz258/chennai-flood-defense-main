from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.models.schemas import (
    CitizenReportRequest,
    CitizenReportResponse,
    DamageEstimateRequest,
    DamageEstimateResponse,
    DeployRequest,
    DeployResponse,
    EvacuationPlanRequest,
    EvacuationPlanResponse,
    ForecastPoint,
    ForecastResponse,
    HealthResponse,
    RecommendationsRequest,
    RecommendationsResponse,
    RouteRequest,
    RouteResponse,
    SendAlertRequest,
    SendAlertResponse,
    SimulationRequest,
    SimulationResponse,
    TrafficRerouteRequest,
    TrafficRerouteResponse,
    ZonesResponse,
)
from backend.app.models.sensor_schema import SensorUpdate, SensorUpdateResponse
from backend.app.services.alert_system import AlertSystemService
from backend.app.services.bigquery_service import forecast_sql_template, to_forecast_rows
from backend.app.services.citizen_reports import CitizenReportsService
from backend.app.services.damage_estimator import DamageEstimatorService
from backend.app.services.decision_engine import DecisionEngineService
from backend.app.services.digital_twin_export import DigitalTwinExportService
from backend.app.services.evacuation_planner import EvacuationPlannerService
from backend.app.services.iot_listener import IoTListenerService
from backend.app.services.system_service import FloodDefenseService
from backend.app.services.traffic_manager import TrafficManagerService

app = FastAPI(title="Chennai Urban Flood Defense API", version="1.0.0")
service = FloodDefenseService()
settings = get_settings()
iot_service = IoTListenerService(service.repo)
citizen_service = CitizenReportsService()
traffic_service = TrafficManagerService()
evacuation_service = EvacuationPlannerService()
damage_service = DamageEstimatorService()
decision_service = DecisionEngineService()
alert_service = AlertSystemService()
digital_twin_service = DigitalTwinExportService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    profile = f"{settings.compute_cpu_vendor} {settings.compute_cpu_family}"
    return HealthResponse(status="ok", service="chennai-flood-defense", compute_profile=profile)


@app.get("/forecast", response_model=ForecastResponse)
def get_forecast() -> ForecastResponse:
    df = service.forecast()
    rows = [ForecastPoint(**item) for item in to_forecast_rows(df)]
    return ForecastResponse(forecast=rows, source="BigQuery AI.FORECAST (TimesFM)")


@app.get("/forecast/sql")
def get_forecast_sql() -> dict:
    return {"sql": forecast_sql_template()}


@app.get("/zones", response_model=ZonesResponse)
def get_zones() -> ZonesResponse:
    zone_df = service.zone_risk()
    return ZonesResponse(zones=zone_df.to_dict(orient="records"))


@app.post("/route", response_model=RouteResponse)
def get_route(request: RouteRequest) -> RouteResponse:
    route_dict, _, _ = service.route(request.source, request.destination)
    return RouteResponse(**route_dict)


@app.post("/deploy", response_model=DeployResponse)
def deploy_units(request: DeployRequest) -> DeployResponse:
    assignments, _ = service.deploy(request.units)
    return DeployResponse(assignments=assignments)


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    units = request.units or []
    (
        multiplier,
        zone_df,
        blocked_roads,
        dispatch,
        route,
        clearance,
        disaster_severity_index,
        recommendations,
    ) = service.simulate(
        rainfall_increase_pct=request.rainfall_increase_pct,
        source=request.source,
        destination=request.destination,
        units=units,
    )
    route_resp = RouteResponse(**route) if route else None
    return SimulationResponse(
        rainfall_multiplier=multiplier,
        zones=zone_df.to_dict(orient="records"),
        blocked_roads=blocked_roads,
        dispatch=dispatch,
        route=route_resp,
        clearance_top5=clearance,
        disaster_severity_index=disaster_severity_index,
        recommendations=recommendations,
    )


@app.post("/sensor-update", response_model=SensorUpdateResponse)
def sensor_update(updates: list[SensorUpdate]) -> SensorUpdateResponse:
    ingested = iot_service.ingest_sensor_updates(updates)
    zone_df = iot_service.recalculate_risk()
    return SensorUpdateResponse(status="processed", records_ingested=ingested, recalculated_zones=len(zone_df))


@app.post("/report", response_model=CitizenReportResponse)
def submit_report(request: CitizenReportRequest) -> CitizenReportResponse:
    saved = citizen_service.store_report(request.model_dump())
    return CitizenReportResponse(status="stored", report=saved)


@app.post("/traffic-reroute", response_model=TrafficRerouteResponse)
def traffic_reroute(request: TrafficRerouteRequest) -> TrafficRerouteResponse:
    zone_df = service.zone_risk()
    reroute = traffic_service.dynamic_reroute(zone_df, request.source, request.destination, request.algorithm)
    return TrafficRerouteResponse(**reroute)


@app.post("/evacuation-plan", response_model=EvacuationPlanResponse)
def evacuation_plan(request: EvacuationPlanRequest) -> EvacuationPlanResponse:
    zone_df = service.zone_risk()
    plans = evacuation_service.create_plan(zone_df, [s.model_dump() for s in request.shelters])
    return EvacuationPlanResponse(plans=plans)


@app.post("/damage-estimate", response_model=DamageEstimateResponse)
def damage_estimate(request: DamageEstimateRequest) -> DamageEstimateResponse:
    estimate = damage_service.estimate(
        flood_depth_cm=request.flood_depth,
        population=request.population,
        infrastructure_density=request.infrastructure_density,
    )
    return DamageEstimateResponse(**estimate.__dict__)


@app.post("/recommendations", response_model=RecommendationsResponse)
def recommendations(request: RecommendationsRequest) -> RecommendationsResponse:
    recs = decision_service.recommend(
        risk_map=request.current_flood_risk_map,
        rescue_units=request.available_rescue_units,
        road_accessibility=request.road_accessibility,
    )
    return RecommendationsResponse(recommendations=recs)


@app.post("/send-alert", response_model=SendAlertResponse)
def send_alert(request: SendAlertRequest) -> SendAlertResponse:
    out = alert_service.send_alert(request.message, request.channels, request.recipients)
    return SendAlertResponse(**out)


@app.get("/digital-twin/export")
def digital_twin_export() -> dict:
    zone_df = service.zone_risk()
    _, blocked = service.routing.build_graph(zone_df)
    deployments, _ = service.deploy([])
    geojson = digital_twin_service.export_geojson(
        flood_zones=zone_df.to_dict(orient="records"),
        blocked_roads=blocked,
        evacuation_routes=[],
        rescue_deployments=deployments,
    )
    return geojson
