import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    project_id: str = ""
    dataset_id: str = "chennai_flood"
    rainfall_table: str = "rainfall_history"
    zones_table: str = "zones"
    gcp_credentials_path: str = ""
    maps_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings(
        project_id=os.getenv("PROJECT_ID", ""),
        dataset_id=os.getenv("DATASET_ID", "chennai_flood"),
        rainfall_table=os.getenv("RAINFALL_TABLE", "rainfall_history"),
        zones_table=os.getenv("ZONES_TABLE", "zones"),
        gcp_credentials_path=os.getenv("GCP_CREDENTIALS_PATH", ""),
        maps_api_key=os.getenv("MAPS_API_KEY", ""),
    )
