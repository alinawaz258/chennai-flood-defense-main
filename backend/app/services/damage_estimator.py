from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DamageEstimate:
    estimated_economic_loss_inr: float
    people_affected: int
    critical_infrastructure_impact: float


class DamageEstimatorService:
    """Computes impact estimates from depth/population/infrastructure metrics."""

    @staticmethod
    def estimate(flood_depth_cm: float, population: int, infrastructure_density: float) -> DamageEstimate:
        depth_factor = max(flood_depth_cm, 0.0) / 100.0
        infra_factor = max(infrastructure_density, 0.0)

        economic_loss = (depth_factor * 6_000_000) + (population * 1500) + (infra_factor * 250_000)
        people_affected = int(population * min(1.0, 0.25 + depth_factor * 0.7))
        critical_impact = min(100.0, (depth_factor * 60.0) + (infra_factor * 5.0))

        return DamageEstimate(
            estimated_economic_loss_inr=round(economic_loss, 2),
            people_affected=people_affected,
            critical_infrastructure_impact=round(critical_impact, 2),
        )
