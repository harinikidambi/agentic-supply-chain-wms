"""Simple semantic representation for demo."""
from scenarios import Scenario

# Simple in-memory semantic representation
AISLE_SEGMENTS = {
    "A-12": {"congested": True, "description": "High traffic aisle with forklift operations"},
    "A-13": {"congested": False, "description": "Moderate traffic aisle"},
    "A-14": {"congested": False, "description": "Low traffic aisle, preferred routing"},
    "X": {"congested": True, "description": "Congested aisle"},
    "Y": {"congested": False, "description": "Clear aisle"}
}


def describe_semantic_context(scenario: Scenario) -> str:
    """
    Returns a short human-readable description that ties scenario attributes
    to semantic ideas like aisle congestion, worker constraints, etc.
    """
    parts = []
    
    # Aisle congestion context
    if scenario.congestion == "high":
        parts.append("Aisle A-12 is highly congested (0.85 congestion score) with multiple forklifts and workers active.")
        parts.append("Aisle A-13 has moderate congestion (0.55).")
        parts.append("Aisle A-14 has low congestion (0.25) and is preferred for routing.")
    elif scenario.congestion == "moderate":
        parts.append("Some aisles show moderate congestion levels.")
    else:
        parts.append("All aisles have low occupancy and minimal congestion.")
    
    # Worker constraints
    if scenario.labor_capacity == "insufficient":
        parts.append("Worker capacity is constrained: fewer workers available than required to meet all promise dates.")
    elif scenario.labor_capacity == "balanced":
        parts.append("Worker capacity is balanced: sufficient workers but tight scheduling required.")
    else:
        parts.append("Worker capacity is sufficient: surplus workers available for flexible scheduling.")
    
    # Inventory confidence
    if scenario.inventory_confidence == "low":
        parts.append("Inventory confidence is low: some locations have conflicting sensor data and system records.")
        parts.append("Locations A-12-05, A-13-08, A-14-03, A-15-07 show discrepancies requiring verification.")
    elif scenario.inventory_confidence == "mixed":
        parts.append("Inventory confidence is mixed: some locations have lower confidence scores.")
    else:
        parts.append("Inventory confidence is normal: all location data is high confidence (0.95+).")
    
    return " ".join(parts)

