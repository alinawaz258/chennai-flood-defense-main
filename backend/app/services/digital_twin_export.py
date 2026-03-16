from __future__ import annotations

from typing import Dict, List


def _feature(geometry_type: str, coordinates, properties: Dict[str, object]) -> Dict[str, object]:
    return {
        "type": "Feature",
        "geometry": {"type": geometry_type, "coordinates": coordinates},
        "properties": properties,
    }


class DigitalTwinExportService:
    """Exports flood operations state to GeoJSON for digital twin ingestion."""

    def export_geojson(
        self,
        flood_zones: List[Dict[str, object]],
        blocked_roads: List[List[str]],
        evacuation_routes: List[Dict[str, object]],
        rescue_deployments: List[Dict[str, object]],
    ) -> Dict[str, object]:
        features: List[Dict[str, object]] = []

        for idx, zone in enumerate(flood_zones):
            features.append(
                _feature(
                    "Point",
                    [80.20 + idx * 0.01, 13.00 + idx * 0.01],
                    {"layer": "flood_zone", **zone},
                )
            )

        for edge in blocked_roads:
            features.append(
                _feature(
                    "LineString",
                    [[80.1, 13.0], [80.15, 13.05]],
                    {"layer": "blocked_road", "source": edge[0], "target": edge[1]},
                )
            )

        for route in evacuation_routes:
            features.append(
                _feature(
                    "LineString",
                    [[80.2, 13.1], [80.22, 13.12]],
                    {"layer": "evacuation_route", **route},
                )
            )

        for dep in rescue_deployments:
            features.append(
                _feature(
                    "Point",
                    [80.25, 13.06],
                    {"layer": "rescue_deployment", **dep},
                )
            )

        return {"type": "FeatureCollection", "features": features}
