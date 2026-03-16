from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


SensorType = Literal["water_level", "rain_gauge", "river_level", "soil_moisture"]


class SensorUpdate(BaseModel):
    """Single IoT telemetry message from field sensors."""

    sensor_id: str = Field(min_length=2, max_length=128)
    sensor_type: SensorType
    zone_id: str = Field(min_length=2, max_length=64)
    value: float
    unit: str = Field(min_length=1, max_length=16)
    timestamp: datetime
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class SensorUpdateResponse(BaseModel):
    """Result of streaming update ingestion and risk refresh."""

    status: str
    records_ingested: int
    recalculated_zones: int
