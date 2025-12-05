"""Simple evaluation logic for PickingAgent decisions."""
from dataclasses import dataclass
from typing import List
from scenarios import Scenario
from picking_agent import ProposedAction


@dataclass
class EvaluationResult:
    """Result of evaluating an agent decision against expectations."""
    passed: bool
    messages: List[str]


def evaluate_decision(scenario: Scenario, action: ProposedAction) -> EvaluationResult:
    """
    Evaluates a ProposedAction against expected behavior for the scenario.
    Returns EvaluationResult with pass/fail and detailed messages.
    """
    messages: List[str] = []
    checks_passed = 0
    total_checks = 0
    
    scenario_id = scenario.id
    
    # Case 1: High SLA + sufficient labor
    if scenario_id == "high_sla_sufficient_labor_low_congestion":
        total_checks += 1
        if not action.escalate:
            messages.append("✓ PASS: Should not escalate when labor is sufficient")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Should not escalate when labor is sufficient")
        
        total_checks += 1
        if "SLA" in action.explanation or "sla" in action.explanation.lower():
            messages.append("✓ PASS: Explanation mentions SLA pressure")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Explanation should mention SLA pressure")
        
        total_checks += 1
        if action.risk_score < 0.5:
            messages.append("✓ PASS: Risk score should be relatively low (< 0.5)")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Risk score should be relatively low (< 0.5)")
    
    # Case 2: High SLA + insufficient labor
    elif scenario_id == "high_sla_insufficient_labor":
        total_checks += 1
        if action.escalate:
            messages.append("✓ PASS: Should escalate when labor is insufficient")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Should escalate when labor is insufficient")
        
        total_checks += 1
        if action.risk_score > 0.5:
            messages.append("✓ PASS: Risk score should be relatively high (> 0.5)")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Risk score should be relatively high (> 0.5)")
        
        total_checks += 1
        if "labor" in action.explanation.lower() or "capacity" in action.explanation.lower():
            messages.append("✓ PASS: Explanation mentions labor/capacity constraints")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Explanation should mention labor/capacity constraints")
    
    # Case 3: Low SLA + high congestion
    elif scenario_id == "low_sla_high_congestion":
        total_checks += 1
        if "congestion" in action.explanation.lower():
            messages.append("✓ PASS: Explanation mentions congestion")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Explanation should mention congestion")
        
        total_checks += 1
        # Should not escalate due to labor (labor is balanced, not insufficient)
        if not action.escalate or (action.escalate and "inventory" in action.explanation.lower()):
            messages.append("✓ PASS: Should not escalate due to labor (labor is balanced)")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Should not escalate due to labor (labor is balanced)")
    
    # Case 4: Inventory confidence issues
    elif scenario_id == "conflicting_partial_data":
        total_checks += 1
        if action.escalate or "inventory" in action.explanation.lower() or "data" in action.explanation.lower() or "confidence" in action.explanation.lower():
            messages.append("✓ PASS: Should escalate or mention inventory/data risk")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Should escalate or mention inventory/data risk")
        
        total_checks += 1
        if action.uncertainty > 0.2:
            messages.append("✓ PASS: Uncertainty should be elevated (> 0.2) for low confidence data")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Uncertainty should be elevated (> 0.2) for low confidence data")
    
    # General checks for all scenarios
    total_checks += 1
    if action.explanation and len(action.explanation) > 20:
        messages.append("✓ PASS: Explanation is provided and meaningful")
        checks_passed += 1
    else:
        messages.append("✗ FAIL: Explanation should be provided and meaningful")
    
    # Determine overall pass/fail
    # Pass if at least 80% of checks pass
    pass_rate = checks_passed / total_checks if total_checks > 0 else 0.0
    passed = pass_rate >= 0.8
    
    return EvaluationResult(
        passed=passed,
        messages=messages
    )

