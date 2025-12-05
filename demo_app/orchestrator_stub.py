"""Minimal orchestrator stub for demo."""
from dataclasses import dataclass
from picking_agent import ProposedAction


@dataclass
class OrchestratorDecision:
    """Represents orchestrator's decision on an agent proposal."""
    auto_approve: bool
    hitl_required: bool
    comment: str


def orchestrate(action: ProposedAction) -> OrchestratorDecision:
    """
    Orchestrator stub that reacts to agent decision.
    This is for demo only, not full orchestrator logic.
    """
    if action.escalate:
        return OrchestratorDecision(
            auto_approve=False,
            hitl_required=True,
            comment=(
                f"Escalation required. Risk score: {action.risk_score:.2f}, "
                f"Uncertainty: {action.uncertainty:.2f}. "
                "Planner intervention needed to resolve capacity constraints or "
                "inventory verification requirements."
            )
        )
    elif action.risk_score > 0.4:
        return OrchestratorDecision(
            auto_approve=True,
            hitl_required=False,
            comment=(
                f"Auto-approved. Risk score: {action.risk_score:.2f} is moderate. "
                "Within policy thresholds but recommend monitoring metrics closely."
            )
        )
    else:
        return OrchestratorDecision(
            auto_approve=True,
            hitl_required=False,
            comment=(
                f"Auto-approved. Low risk score: {action.risk_score:.2f}. "
                "Proceeding with standard operations."
            )
        )

