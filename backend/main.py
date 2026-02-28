from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models.schemas import (
    DeployRequest,
    DeployResponse,
    ForecastPoint,
    ForecastResponse,
    HealthResponse,
    RouteRequest,
    RouteResponse,
    SimulationRequest,
    SimulationResponse,
    ZonesResponse,
)
from backend.app.services.bigquery_service import forecast_sql_template, to_forecast_rows
from backend.app.services.system_service import FloodDefenseService

app = FastAPI(title="Chennai Urban Flood Defense API", version="1.0.0")
service = FloodDefenseService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", service="chennai-flood-defense")


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
    multiplier, zone_df, blocked_roads, dispatch, route, clearance = service.simulate(
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
    )
