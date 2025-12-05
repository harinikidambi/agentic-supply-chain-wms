"""Simple evaluation logic for PickingAgent decisions."""
from dataclasses import dataclass
from typing import List, Dict, Any
from scenarios import Scenario, EXPECTATIONS
from picking_agent import ProposedAction
from tools import estimate_inventory_confidence_risk


@dataclass
class EvaluationResult:
    """Result of evaluating an agent decision against expectations."""
    passed: bool
    messages: List[str]
    status: str  # "PASS" | "FAIL"
    details: List[Dict[str, Any]]  # List of check results with pass, description
    expected: Dict[str, Any]  # Expected values for this scenario
    actual: Dict[str, Any]  # Actual values from agent


def evaluate_decision(scenario: Scenario, action: ProposedAction) -> EvaluationResult:
    """
    Evaluates a ProposedAction against expected behavior for the scenario.
    Returns EvaluationResult with pass/fail and detailed messages.
    """
    messages: List[str] = []
    details: List[Dict[str, Any]] = []
    checks_passed = 0
    total_checks = 0
    
    scenario_id = scenario.id
    expected = {}
    actual = {
        "action_type": action.action_type,
        "escalate": action.escalate,
        "uncertainty": action.uncertainty,
        "risk_score": action.risk_score,
        "explanation": action.explanation
    }
    
    # Case 1: High SLA + sufficient labor
    if scenario_id == "high_sla_sufficient_labor_low_congestion":
        total_checks += 1
        check_passed = not action.escalate
        details.append({
            "pass": check_passed,
            "description": "Should not escalate when labor is sufficient"
        })
        if check_passed:
            messages.append("✓ PASS: Should not escalate when labor is sufficient")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Should not escalate when labor is sufficient")
        
        total_checks += 1
        check_passed = "SLA" in action.explanation or "sla" in action.explanation.lower()
        details.append({
            "pass": check_passed,
            "description": "Explanation mentions SLA pressure"
        })
        if check_passed:
            messages.append("✓ PASS: Explanation mentions SLA pressure")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Explanation should mention SLA pressure")
        
        total_checks += 1
        # Align with orchestrator's low risk threshold (<= 0.4) for sufficient labor scenario
        check_passed = action.risk_score <= 0.4
        details.append({
            "pass": check_passed,
            "description": "Risk score should be relatively low (<= 0.4, aligning with orchestrator threshold)"
        })
        if check_passed:
            messages.append("✓ PASS: Risk score should be relatively low (<= 0.4)")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Risk score should be relatively low (<= 0.4)")
    
    # Case 2: High SLA + insufficient labor
    elif scenario_id == "high_sla_insufficient_labor":
        total_checks += 1
        check_passed = action.escalate
        details.append({
            "pass": check_passed,
            "description": "Should escalate when labor is insufficient"
        })
        if check_passed:
            messages.append("✓ PASS: Should escalate when labor is insufficient")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Should escalate when labor is insufficient")
        
        total_checks += 1
        # Use >= 0.5 to avoid boundary condition with Case 1 (<= 0.4) and ensure clear separation
        check_passed = action.risk_score >= 0.5
        details.append({
            "pass": check_passed,
            "description": "Risk score should be relatively high (>= 0.5, insufficient labor scenario)"
        })
        if check_passed:
            messages.append("✓ PASS: Risk score should be relatively high (>= 0.5)")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Risk score should be relatively high (>= 0.5)")
        
        total_checks += 1
        check_passed = "labor" in action.explanation.lower() or "capacity" in action.explanation.lower()
        details.append({
            "pass": check_passed,
            "description": "Explanation mentions labor/capacity constraints"
        })
        if check_passed:
            messages.append("✓ PASS: Explanation mentions labor/capacity constraints")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Explanation should mention labor/capacity constraints")
    
    # Case 3: Low SLA + high congestion
    elif scenario_id == "low_sla_high_congestion":
        total_checks += 1
        check_passed = "congestion" in action.explanation.lower()
        details.append({
            "pass": check_passed,
            "description": "Explanation mentions congestion"
        })
        if check_passed:
            messages.append("✓ PASS: Explanation mentions congestion")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Explanation should mention congestion")
        
        total_checks += 1
        # Should not escalate due to labor (labor is balanced, not insufficient)
        check_passed = not action.escalate or (action.escalate and "inventory" in action.explanation.lower())
        details.append({
            "pass": check_passed,
            "description": "Should not escalate due to labor (labor is balanced)"
        })
        if check_passed:
            messages.append("✓ PASS: Should not escalate due to labor (labor is balanced)")
            checks_passed += 1
        else:
            messages.append("✗ FAIL: Should not escalate due to labor (labor is balanced)")
    
    # Case 4: Inventory confidence issues - with explicit expectations
    elif scenario_id == "conflicting_partial_data":
        expectations = EXPECTATIONS.get(scenario_id, {})
        expected["action_type"] = expectations.get("expected_action", "request_inventory_checks")
        expected["escalate"] = expectations.get("expected_escalation", True)
        expected["uncertainty_min"] = expectations.get("expected_uncertainty_min", 0.2)
        expected["should_not_proceed_with_picking"] = expectations.get("should_not_proceed_with_picking", True)
        
        # Check 1: Should escalate when inventory confidence is LOW and uncertainty > 0.2
        total_checks += 1
        should_escalate = expected["escalate"]
        uncertainty_threshold = expected["uncertainty_min"]
        inventory_risk = estimate_inventory_confidence_risk(scenario) if hasattr(scenario, 'inventory_confidence') else 0.6
        
        escalation_check_passed = action.escalate == should_escalate
        if escalation_check_passed:
            details.append({
                "pass": True,
                "description": f"Should escalate when inventory confidence is LOW and uncertainty > {uncertainty_threshold}"
            })
            messages.append("✓ PASS: Should escalate when inventory confidence is LOW and uncertainty > 0.2")
            checks_passed += 1
        else:
            details.append({
                "pass": False,
                "description": f"Should escalate when inventory confidence is LOW and uncertainty > {uncertainty_threshold}. Agent did not escalate despite LOW inventory confidence and uncertainty > {uncertainty_threshold}."
            })
            messages.append("✗ FAIL: Should escalate when inventory confidence is LOW and uncertainty > 0.2")
        
        # Check 2: Action should not be 'Proceed With Picking' when there are unresolved data conflicts
        total_checks += 1
        should_not_proceed = expected["should_not_proceed_with_picking"]
        action_check_passed = action.action_type != "proceed_with_picking" if should_not_proceed else True
        if action_check_passed:
            details.append({
                "pass": True,
                "description": "Action should not be 'Proceed With Picking' when there are unresolved data conflicts"
            })
            messages.append("✓ PASS: Action should not be 'Proceed With Picking' when there are unresolved data conflicts")
            checks_passed += 1
        else:
            details.append({
                "pass": False,
                "description": "Action should not be 'Proceed With Picking' when there are unresolved data conflicts. Agent chose to proceed despite data conflicts."
            })
            messages.append("✗ FAIL: Action should not be 'Proceed With Picking' when there are unresolved data conflicts")
        
        # Check 3: Explanation should mention inventory or data discrepancy risk
        total_checks += 1
        explanation_keywords = expectations.get("expected_explanation_keywords", ["inventory", "data", "confidence"])
        explanation_lower = action.explanation.lower()
        keyword_found = any(keyword in explanation_lower for keyword in explanation_keywords)
        if keyword_found:
            details.append({
                "pass": True,
                "description": "Explanation should mention inventory or data discrepancy risk"
            })
            messages.append("✓ PASS: Explanation mentions inventory or data discrepancy risk")
            checks_passed += 1
        else:
            details.append({
                "pass": False,
                "description": "Explanation should mention inventory or data discrepancy risk. Agent explanation lacks mention of data/inventory concerns."
            })
            messages.append("✗ FAIL: Explanation should mention inventory or data discrepancy risk")
        
        # Check 4: Uncertainty should be elevated for low confidence data
        total_checks += 1
        uncertainty_check_passed = action.uncertainty > expected["uncertainty_min"]
        if uncertainty_check_passed:
            details.append({
                "pass": True,
                "description": f"Uncertainty should be elevated (> {expected['uncertainty_min']}) for low confidence data"
            })
            messages.append(f"✓ PASS: Uncertainty should be elevated (> {expected['uncertainty_min']}) for low confidence data")
            checks_passed += 1
        else:
            details.append({
                "pass": False,
                "description": f"Uncertainty should be elevated (> {expected['uncertainty_min']}) for low confidence data. Actual uncertainty: {action.uncertainty:.2f}"
            })
            messages.append(f"✗ FAIL: Uncertainty should be elevated (> {expected['uncertainty_min']}) for low confidence data")
    
    # General checks for all scenarios
    total_checks += 1
    check_passed = action.explanation and len(action.explanation) > 20
    if not details:  # Only add if details weren't populated above
        details.append({
            "pass": check_passed,
            "description": "Explanation is provided and meaningful"
        })
    if check_passed:
        messages.append("✓ PASS: Explanation is provided and meaningful")
        checks_passed += 1
    else:
        messages.append("✗ FAIL: Explanation should be provided and meaningful")
    
    # Determine overall pass/fail
    # For scenarios with explicit expectations, require all critical checks to pass
    # For other scenarios, pass if at least 80% of checks pass
    if scenario_id in EXPECTATIONS:
        # For explicit expectations, fail if any check fails
        passed = checks_passed == total_checks
    else:
        pass_rate = checks_passed / total_checks if total_checks > 0 else 0.0
        passed = pass_rate >= 0.8
    
    status = "PASS" if passed else "FAIL"
    
    # If no explicit expectations were set, populate expected with defaults
    if not expected:
        expected = {
            "action_type": "varies",
            "escalate": "varies",
            "uncertainty_min": 0.0,
            "risk_range": "varies"
        }
    
    # If details weren't populated, create them from messages
    if not details:
        details = [{"pass": "✓" in msg, "description": msg.replace("✓ PASS: ", "").replace("✗ FAIL: ", "")} for msg in messages]
    
    return EvaluationResult(
        passed=passed,
        messages=messages,
        status=status,
        details=details,
        expected=expected,
        actual=actual
    )

