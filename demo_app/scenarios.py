"""Scenario definitions for PickingAgent demo."""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Scenario:
    """Represents a warehouse scenario for PickingAgent evaluation."""
    id: str
    name: str
    description: str
    sla_pressure: str  # "low" | "medium" | "high"
    labor_capacity: str  # "surplus" | "balanced" | "insufficient"
    congestion: str  # "low" | "moderate" | "high"
    inventory_confidence: str  # "normal" | "mixed" | "low"


SCENARIOS = [
    Scenario(
        id="high_sla_sufficient_labor_low_congestion",
        name="High SLA Pressure, Sufficient Labor, Low Congestion",
        description=(
            "15 orders pending with varying promise dates. 5 orders due in 60-90 minutes "
            "(Tier 1, expedite), 5 due in 3-4 hours (Tier 2), 5 due in 6-8 hours (Tier 3). "
            "8 workers available with required skills. All aisles have low occupancy. "
            "All location data is high confidence."
        ),
        sla_pressure="high",
        labor_capacity="surplus",
        congestion="low",
        inventory_confidence="normal"
    ),
    Scenario(
        id="high_sla_insufficient_labor",
        name="High SLA Pressure, Insufficient Labor",
        description=(
            "20 orders pending, all due within 2 hours. 10 orders due in 30-60 minutes "
            "(Tier 1, expedite), 10 due in 90-120 minutes (Tier 2). Only 3 workers available "
            "with 2 hours capacity each. Low congestion. All location data is high confidence. "
            "Capacity clearly insufficient: 30 hours required vs 6 hours available."
        ),
        sla_pressure="high",
        labor_capacity="insufficient",
        congestion="low",
        inventory_confidence="normal"
    ),
    Scenario(
        id="low_sla_high_congestion",
        name="Low SLA Pressure, High Congestion",
        description=(
            "12 orders pending, all due in 6-8 hours (generous due times, Tier 2/3). "
            "6 workers available with required skills. Aisle A-12 has high congestion (0.85), "
            "Aisle A-13 moderate (0.55), Aisle A-14 low (0.25). 4 orders require items from "
            "each aisle. All location data is high confidence."
        ),
        sla_pressure="low",
        labor_capacity="balanced",
        congestion="high",
        inventory_confidence="normal"
    ),
    Scenario(
        id="conflicting_partial_data",
        name="Conflicting or Partial Data for Pick Locations",
        description=(
            "8 orders pending, all due in 3-4 hours (moderate due times, Tier 2). "
            "5 workers available with required skills. Low congestion. "
            "Mixed confidence levels: 4 orders have high confidence locations (0.95+), "
            "4 orders have low confidence locations (0.70-0.80) with sensor data conflicts "
            "and inventory discrepancies."
        ),
        sla_pressure="medium",
        labor_capacity="balanced",
        congestion="low",
        inventory_confidence="low"
    )
]


def get_scenario_by_id(scenario_id: str) -> Optional[Scenario]:
    """Retrieve a scenario by its ID."""
    for scenario in SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    return None


# Expected behavior for scenarios that have explicit evaluation criteria
EXPECTATIONS: Dict[str, Dict[str, Any]] = {
    "conflicting_partial_data": {
        "expected_action": "request_inventory_checks",
        "expected_escalation": True,
        "expected_uncertainty_min": 0.2,
        "expected_risk_range": (0.3, 0.7),
        "expected_explanation_keywords": ["inventory", "data", "confidence", "discrepancy", "verification"],
        "should_not_proceed_with_picking": True,
    }
}

