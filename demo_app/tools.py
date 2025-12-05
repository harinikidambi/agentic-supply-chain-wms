"""Simple deterministic tool functions for risk estimation."""
from scenarios import Scenario


def estimate_sla_risk(s: Scenario) -> float:
    """
    Returns a 0-1 score based on sla_pressure and labor_capacity.
    Higher score indicates higher SLA risk.
    """
    sla_map = {"low": 0.2, "medium": 0.5, "high": 0.9}
    labor_map = {"surplus": 0.0, "balanced": 0.2, "insufficient": 0.6}
    
    base_risk = sla_map.get(s.sla_pressure, 0.5)
    labor_penalty = labor_map.get(s.labor_capacity, 0.2)
    
    # Combine: high SLA pressure with insufficient labor = very high risk
    risk = min(1.0, base_risk + labor_penalty)
    return round(risk, 2)


def estimate_labor_feasibility(s: Scenario) -> float:
    """
    Returns 1.0 for fully feasible, 0.0 for clearly impossible.
    Uses labor_capacity and sla_pressure to compute.
    """
    labor_map = {"surplus": 1.0, "balanced": 0.8, "insufficient": 0.3}
    sla_map = {"low": 1.0, "medium": 0.9, "high": 0.7}
    
    base_feasibility = labor_map.get(s.labor_capacity, 0.5)
    sla_adjustment = sla_map.get(s.sla_pressure, 0.8)
    
    # High SLA pressure reduces feasibility even with balanced labor
    feasibility = base_feasibility * sla_adjustment
    return round(feasibility, 2)


def estimate_congestion_risk(s: Scenario) -> float:
    """Maps congestion to 0-1 risk score."""
    congestion_map = {"low": 0.1, "moderate": 0.4, "high": 0.7}
    return congestion_map.get(s.congestion, 0.3)


def estimate_inventory_confidence_risk(s: Scenario) -> float:
    """
    Returns 0 for "normal", higher for "mixed" or "low".
    """
    confidence_map = {"normal": 0.0, "mixed": 0.3, "low": 0.6}
    return confidence_map.get(s.inventory_confidence, 0.0)

