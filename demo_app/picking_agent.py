"""PickingAgent implementation for demo."""
from dataclasses import dataclass
from typing import List
from scenarios import Scenario
from tools import (
    estimate_sla_risk,
    estimate_labor_feasibility,
    estimate_congestion_risk,
    estimate_inventory_confidence_risk
)


@dataclass
class ProposedAction:
    """Represents a proposed action from PickingAgent."""
    action_type: str
    prioritised_orders: List[str]
    deferred_orders: List[str]
    risk_score: float
    uncertainty: float
    escalate: bool
    explanation: str
    reasoning_summary: str  # Human-readable summary of agent's reasoning


class PickingAgent:
    """Hero PickingAgent that makes decisions based on warehouse scenarios."""
    
    def decide(self, scenario: Scenario) -> ProposedAction:
        """
        Makes a decision based on the scenario.
        Returns a ProposedAction with risk assessment and explanation.
        """
        # Gather signals from tools
        sla_risk = estimate_sla_risk(scenario)
        labor_feasibility = estimate_labor_feasibility(scenario)
        congestion_risk = estimate_congestion_risk(scenario)
        inventory_confidence_risk = estimate_inventory_confidence_risk(scenario)
        
        # Combine into overall risk score
        # Weight SLA risk and labor feasibility most heavily
        risk_score = (sla_risk * 0.4 + (1.0 - labor_feasibility) * 0.3 + 
                     congestion_risk * 0.2 + inventory_confidence_risk * 0.1)
        risk_score = min(1.0, risk_score)
        
        # Uncertainty: higher when signals are conflicting or severe
        # High uncertainty if labor is insufficient OR inventory confidence is low
        uncertainty = 0.0
        if labor_feasibility < 0.5:
            uncertainty += 0.3
        if inventory_confidence_risk > 0.4:
            uncertainty += 0.3
        if congestion_risk > 0.5 and scenario.sla_pressure == "high":
            uncertainty += 0.2  # Conflicting priorities
        uncertainty = min(1.0, uncertainty)
        
        # Determine action type
        if scenario.sla_pressure == "high" and labor_feasibility >= 0.7:
            action_type = "prioritise_critical_orders"
            prioritised_orders = ["critical_tier1_60min", "critical_tier1_90min"]
            deferred_orders = ["low_priority_batch"]
        elif labor_feasibility < 0.5:
            action_type = "defer_low_priority_work"
            prioritised_orders = ["critical_only"]
            deferred_orders = ["standard_priority_batch", "low_priority_batch"]
        elif inventory_confidence_risk > 0.4:
            action_type = "request_inventory_checks"
            prioritised_orders = ["high_confidence_orders"]
            deferred_orders = ["low_confidence_orders"]
        elif congestion_risk > 0.5:
            action_type = "normal_wave_planning"
            prioritised_orders = ["non_congested_aisles"]
            deferred_orders = ["congested_aisles"]
        else:
            action_type = "normal_wave_planning"
            prioritised_orders = ["standard_batch"]
            deferred_orders = []
        
        # Escalation logic
        escalate = False
        if labor_feasibility < 0.5:
            escalate = True
        if inventory_confidence_risk > 0.4:
            escalate = True
        
        # INTENTIONAL FAILURE: For conflicting_partial_data scenario, make a bad decision
        # This demonstrates evaluation catching unsafe behavior
        if scenario.id == "conflicting_partial_data":
            # Wrong decision: proceed with picking despite low confidence
            action_type = "proceed_with_picking"
            prioritised_orders = ["all_orders"]
            deferred_orders = []
            escalate = False  # Should escalate but doesn't
            # Create a plausible but wrong reasoning
            reasoning_summary = (
                "Agent assumes discrepancies are minor and proceeds without verification. "
                "Inventory confidence is mixed but within acceptable range for standard operations. "
                "Proceeding with picking to meet SLA targets."
            )
        else:
            # Normal reasoning summary for other scenarios
            reasoning_parts = []
            if scenario.sla_pressure == "high":
                reasoning_parts.append(f"High SLA pressure ({sla_risk:.2f} risk) requires prioritization.")
            if labor_feasibility < 0.7:
                reasoning_parts.append(f"Labor capacity concerns ({labor_feasibility:.2f} feasibility) may require escalation.")
            if inventory_confidence_risk > 0.3:
                reasoning_parts.append(f"Inventory confidence issues ({inventory_confidence_risk:.2f} risk) need verification.")
            if congestion_risk > 0.4:
                reasoning_parts.append(f"Congestion risk ({congestion_risk:.2f}) affects routing decisions.")
            if escalate:
                reasoning_parts.append("Escalation required due to high risk or uncertainty.")
            else:
                reasoning_parts.append("All constraints within acceptable thresholds for autonomous operation.")
            
            reasoning_summary = " ".join(reasoning_parts) if reasoning_parts else "Standard operation proceeding normally."
        
        # Build explanation
        explanation_parts = []
        explanation_parts.append(f"SLA Pressure: {scenario.sla_pressure.upper()} (risk score: {sla_risk:.2f})")
        explanation_parts.append(f"Labor Capacity: {scenario.labor_capacity} (feasibility: {labor_feasibility:.2f})")
        
        if congestion_risk > 0.2:
            explanation_parts.append(f"Congestion: {scenario.congestion} (risk: {congestion_risk:.2f})")
        
        if inventory_confidence_risk > 0.1:
            explanation_parts.append(f"Inventory Confidence: {scenario.inventory_confidence} (risk: {inventory_confidence_risk:.2f})")
        
        if escalate:
            if labor_feasibility < 0.5:
                explanation_parts.append("ESCALATING: Insufficient labor capacity to meet all promise dates.")
            if inventory_confidence_risk > 0.4:
                explanation_parts.append("ESCALATING: Low inventory confidence requires verification before picking.")
        else:
            explanation_parts.append("Proceeding autonomously: All constraints within acceptable thresholds.")
        
        explanation = "\n".join(explanation_parts)
        
        return ProposedAction(
            action_type=action_type,
            prioritised_orders=prioritised_orders,
            deferred_orders=deferred_orders,
            risk_score=round(risk_score, 2),
            uncertainty=round(uncertainty, 2),
            escalate=escalate,
            explanation=explanation,
            reasoning_summary=reasoning_summary
        )

