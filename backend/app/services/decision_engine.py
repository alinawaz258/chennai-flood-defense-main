from __future__ import annotations

from typing import Dict, List


class DecisionEngineService:
    """Generates operational recommendations from risk/resources/accessibility."""

    def recommend(
        self,
        risk_map: List[Dict[str, object]],
        rescue_units: List[Dict[str, object]],
        road_accessibility: List[Dict[str, object]],
    ) -> List[str]:
        recommendations: List[str] = []
        high_risk = [z for z in risk_map if float(z.get("flood_probability", 0)) >= 0.75]
        blocked = [r for r in road_accessibility if not bool(r.get("accessible", True))]

        if high_risk:
            recommendations.append(f"Deploy rescue units to {len(high_risk)} critical zones")

        if len(rescue_units) < len(high_risk):
            recommendations.append("Request mutual aid units from neighboring districts")

        if blocked:
            roads = ", ".join(str(r.get("road_id", "unknown")) for r in blocked[:5])
            recommendations.append(f"Close unsafe roads immediately: {roads}")

        if any(z.get("risk_level") in {"HIGH", "CRITICAL"} for z in risk_map):
            recommendations.append("Open nearest shelters and broadcast precautionary alerts")

        if not recommendations:
            recommendations.append("Continue monitoring; no immediate escalation required")
        return recommendations
