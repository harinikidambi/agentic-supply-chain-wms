"""
WMS Orchestrator Logic: Behavior Specification for Hybrid Agentic WMS

This file contains PSEUDOCODE behavior specifications for the WMS Orchestrator in the
hybrid Warehouse Management System architecture. This is NOT production-ready code,
but rather a behavioral specification that engineers can use to implement orchestrator logic.

Purpose:
--------
- Define how the Orchestrator evaluates micro-agent proposals
- Encode conflict detection, safety checks, and SLA reasoning
- Specify decision logic for auto-approval, rescheduling, rejection, and HITL escalation
- Serve as a bridge between architecture specifications and implementation

Role in Hybrid Architecture:
----------------------------
The Orchestrator is the central coordination layer that:

1. **Collects proposals** from specialized micro-agents (Picking, Replenishment, Slotting,
   Labor, Dock/Yard, Inventory Accuracy agents)

2. **Evaluates against global state** by querying the Semantic Warehouse Graph to understand
   current warehouse state, active operations, and constraints

3. **Detects conflicts** when multiple agents propose actions that compete for constrained
   resources (aisles, workers, forklifts, doors, inventory) or violate safety/SLA rules

4. **Resolves conflicts** by applying arbitration rules that prioritize:
   - Safety first (no violations of physical safety rules)
   - SLA adherence (high-priority orders, promise dates, cut-off times)
   - Operational optimization (minimize total delay, maximize throughput)

5. **Routes to HITL** when risk exceeds thresholds, confidence is low, or tradeoffs require
   human judgment. The Orchestrator builds structured decision requests that planners review
   in the conflict resolution UX flow.

6. **Finalizes actions** by converting approved resolutions into ApprovedAction objects that
   are sent to deterministic execution engines

Relationship to Other Components:
----------------------------------
- **Micro-Agents:** Generate ProposedAction objects based on local domain optimization
- **Semantic Warehouse Graph:** Provides current state, constraint validation, conflict detection
- **Deterministic Engines:** Verify critical paths, provide safety guarantees
- **Planner (HITL):** Reviews high-risk conflicts, approves/rejects/modifies resolutions
- **Execution Layer:** Receives ApprovedAction objects and executes physical operations

This is Pseudocode:
------------------
This file uses Python-style syntax for clarity, but is NOT executable production code.
Engineers should:
1. Use this as a behavior specification
2. Implement actual logic using appropriate frameworks (LLM orchestration, constraint solvers)
3. Extend data structures to include production requirements (IDs, timestamps, audit fields)
4. Add error handling, retries, and observability hooks
5. Integrate with actual Semantic Warehouse Graph queries and event bus communication
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

# Import ProposedAction from microagent_behaviors.py
# In production, this would be a proper import from the microagent module
# from prototype.microagent_behaviors import ProposedAction


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class ConflictGroup:
    """
    Represents a set of ProposedAction objects that conflict with each other.
    
    Conflicts occur when proposals compete for:
    - Same physical space (aisle, location, door)
    - Same resources (worker, forklift, equipment)
    - Overlapping time windows with incompatible operations
    - Safety rule violations (forklift-worker proximity, aisle occupancy)
    - SLA tradeoffs (multiple orders at risk)
    
    Attributes:
        conflict_id: Unique identifier for this conflict group
        conflicting_proposals: List of ProposedAction objects that conflict
        conflict_type: Type of conflict (aisle_occupancy, resource_competition, etc.)
        conflict_location: Physical location where conflict occurs (aisle, zone, door)
        conflict_time_window: Time window where conflict occurs
        detected_at: Timestamp when conflict was detected
        risk_score: Overall risk score for this conflict (0.0-1.0)
    """
    conflict_id: str
    conflicting_proposals: List[Any]  # List[ProposedAction] in production
    conflict_type: str  # e.g., "aisle_occupancy", "resource_competition", "sla_tradeoff"
    conflict_location: str  # e.g., "Aisle A-12", "Dock Door 5"
    conflict_time_window: Dict[str, datetime]  # earliest_start, latest_end
    detected_at: datetime
    risk_score: float  # 0.0-1.0, aggregated from proposal risk scores


@dataclass
class ResolutionDecision:
    """
    Represents the Orchestrator's decision on how to resolve a conflict group.
    
    The decision encodes:
    - Which proposals to approve (auto-approve)
    - Which proposals to reschedule (new time window or location)
    - Which proposals to reject (cannot proceed)
    - Whether to escalate to HITL (human planner)
    
    Attributes:
        decision_id: Unique identifier for this resolution
        conflict_group: The ConflictGroup this resolution addresses
        approved_proposals: List of proposals approved to proceed as-is
        rescheduled_proposals: Dict mapping proposal_id to new time_window/location
        rejected_proposals: List of proposals rejected with reason
        escalation_required: Whether this decision requires HITL review
        rationale: Explanation of why this resolution was chosen
        confidence: Orchestrator's confidence in this resolution (0.0-1.0)
        safety_risk: Safety risk score after resolution (0.0-1.0)
        sla_risk: SLA risk score after resolution (0.0-1.0)
        operational_impact: Estimated delay/throughput impact
    """
    decision_id: str
    conflict_group: ConflictGroup
    approved_proposals: List[Any]  # List[ProposedAction]
    rescheduled_proposals: Dict[str, Dict[str, Any]]  # proposal_id -> {new_time_window, new_location, reason}
    rejected_proposals: Dict[str, str]  # proposal_id -> rejection_reason
    escalation_required: bool
    rationale: str
    confidence: float  # 0.0-1.0
    safety_risk: float  # 0.0-1.0
    sla_risk: float  # 0.0-1.0
    operational_impact: Dict[str, Any]  # delay_minutes, throughput_impact, etc.


@dataclass
class WarehouseState:
    """
    Placeholder for global warehouse state that Orchestrator queries.
    
    In production, this would be implemented as queries to:
    - Semantic Warehouse Graph (entities, relationships, constraints)
    - Real-time sensor data (aisle occupancy, location status)
    - Active operations (current tasks, scheduled operations)
    - Safety flags (aisle locks, maintenance windows, incidents)
    - SLA status (order promise dates, cut-off times, priority tiers)
    """
    # Aisle/zone state
    aisle_occupancy: Dict[str, str]  # aisle_id -> "empty" | "occupied" | "locked"
    aisle_capacity: Dict[str, int]  # aisle_id -> max_concurrent_operations
    worker_density: Dict[str, float]  # zone_id -> workers_per_100sqft
    
    # Resource availability
    worker_availability: Dict[str, bool]  # worker_id -> available
    forklift_availability: Dict[str, bool]  # forklift_id -> available
    equipment_status: Dict[str, str]  # equipment_id -> "operational" | "maintenance"
    
    # Safety state
    safety_locks: List[str]  # list of locked aisle/location IDs
    maintenance_windows: Dict[str, tuple]  # location_id -> (start_time, end_time)
    
    # SLA state
    active_orders: List[Dict[str, Any]]  # order_id, promise_date, priority_tier
    order_sla_status: Dict[str, str]  # order_id -> "on_track" | "at_risk" | "violated"
    
    # Time context
    current_time: datetime
    peak_hours: List[tuple]  # list of (start_hour, end_hour) tuples


@dataclass
class PlannerDecisionRequest:
    """
    Payload sent to planner (HITL) for conflict resolution review.
    
    This structure is what the planner sees in the conflict resolution UX flow.
    Contains all information needed for planner to make informed decision.
    """
    request_id: str
    conflict_summary: str  # High-level description of conflict
    agents_involved: List[str]  # List of agent names
    location: str  # Physical location of conflict
    time_window: Dict[str, datetime]
    risk_indicators: Dict[str, float]  # safety_risk, sla_risk, operational_impact
    proposals: List[Dict[str, Any]]  # Detailed proposal information
    orchestrator_recommendation: ResolutionDecision
    impact_preview: Dict[str, Any]  # SLA impact, congestion projection, operational metrics
    alternatives: List[Dict[str, Any]]  # Alternative resolutions considered
    confidence: float  # Orchestrator's confidence in recommendation
    detected_at: datetime


@dataclass
class ApprovedAction:
    """
    Final action approved by Orchestrator (or planner) to be executed.
    
    This is what gets sent to deterministic execution engines.
    """
    action_id: str
    original_proposal: Any  # ProposedAction
    approved_time_window: Dict[str, datetime]
    approved_resources: List[str]
    execution_priority: int
    safety_validated: bool
    sla_validated: bool
    approved_by: str  # "orchestrator" | "planner:{user_id}"
    approved_at: datetime


# ============================================================================
# WMS Orchestrator Class
# ============================================================================

class WMSOrchestrator:
    """
    Central coordination layer for hybrid agentic WMS.
    
    The Orchestrator's personality (from agent_design/agent_personalities.md):
    - Safety-first: Never compromises on safety rules
    - Balanced on SLA vs congestion: Can defer lower-priority work to protect high-priority orders
    - Defaults to HITL when tradeoffs are ambiguous or high-impact
    - Prefers deterministic, explainable decisions
    - Acts as referee and judge, not a player (doesn't generate proposals)
    
    Key Responsibilities:
    1. Collect and validate proposals from micro-agents
    2. Detect conflicts using semantic graph queries
    3. Apply safety and SLA rules
    4. Resolve conflicts using arbitration rules
    5. Route to HITL when risk/uncertainty exceeds thresholds
    6. Finalize approved actions for execution
    """
    
    def __init__(self):
        """
        Initialize Orchestrator with configuration.
        
        In production, this would load:
        - Safety rule definitions
        - SLA thresholds and policies
        - Arbitration rule configurations
        - HITL escalation thresholds
        - Semantic graph connection
        - Event bus connection
        """
        # Configuration (would be loaded from config in production)
        self.safety_risk_threshold = 0.1  # Escalate if safety risk > 0.1
        self.sla_risk_threshold = 0.2  # Escalate if SLA risk > 0.2
        self.confidence_threshold = 0.95  # Escalate if confidence < 0.95
        self.complexity_threshold = 2  # Escalate if > 2 agents in conflict
        
        # State tracking (in production, would query semantic graph instead)
        self.active_proposals: List[Any] = []  # List[ProposedAction]
        self.resolved_conflicts: List[ConflictGroup] = []
        self.pending_hitl_requests: List[PlannerDecisionRequest] = []
        
        # Arbitration rules (would be loaded from policy config in production)
        self.arbitration_rules = {
            "safety_first": True,  # Safety violations cannot be overridden
            "sla_priority": True,  # Tier 1 > Tier 2 > Tier 3, Expedite > Standard
            "temporal_ordering": True,  # First-come-first-served for equal priority
            "resource_optimization": True,  # Minimize total delay across operations
        }
    
    def collect_proposals(self, proposals: List[Any]) -> List[Any]:
        """
        Performs basic validation and filtering of proposals from micro-agents.
        
        Inputs:
        - proposals: List of ProposedAction objects from micro-agents
        
        Process:
        1. Validate proposal schema (required fields present, types correct)
        2. Check for stale proposals (time window expired, global state changed)
        3. Filter out proposals with missing or inconsistent metadata
        4. Check for duplicate proposals (same agent, same action, same time)
        5. Validate against basic constraints (aisle locks, maintenance windows)
        
        Returns:
        - List of valid proposals ready for conflict detection
        
        Edge Cases Handled:
        - Stale proposals: If proposal's time window has passed or global state
          changed significantly since proposal was generated, reject with error
        - Missing metadata: If required fields (confidence, risk_score, etc.) are
          missing, reject with error asking agent to regenerate
        - Duplicate proposals: If same agent submits same proposal twice, keep only
          the most recent one
        """
        valid_proposals = []
        current_time = datetime.now()  # In production, get from WarehouseState
        
        for proposal in proposals:
            # Step 1: Schema validation
            if not self._validate_proposal_schema(proposal):
                # Log error: "Proposal {proposal_id} missing required fields"
                # Notify agent to regenerate proposal
                continue
            
            # Step 2: Check for stale proposals
            if self._is_proposal_stale(proposal, current_time):
                # Log: "Proposal {proposal_id} stale, time window expired or state changed"
                # Notify agent: "Proposal stale, please regenerate with current state"
                continue
            
            # Step 3: Check for missing or inconsistent metadata
            if not self._has_complete_metadata(proposal):
                # Log: "Proposal {proposal_id} missing metadata: {missing_fields}"
                # Notify agent: "Proposal incomplete, please regenerate with all metadata"
                continue
            
            # Step 4: Check for duplicates
            if self._is_duplicate_proposal(proposal):
                # Log: "Proposal {proposal_id} duplicate, keeping most recent"
                # Remove older duplicate from active_proposals
                self._remove_duplicate(proposal)
            
            # Step 5: Basic constraint validation
            if not self._passes_basic_constraints(proposal):
                # Log: "Proposal {proposal_id} violates basic constraints: {violations}"
                # Notify agent: "Proposal violates constraints, please regenerate"
                continue
            
            # Proposal is valid, add to active list
            valid_proposals.append(proposal)
            self.active_proposals.append(proposal)
        
        return valid_proposals
    
    def detect_conflicts(self, proposals: List[Any], global_state: WarehouseState) -> List[ConflictGroup]:
        """
        Groups proposals that compete for constrained resources or violate safety/SLA rules.
        
        Inputs:
        - proposals: List of valid ProposedAction objects
        - global_state: Current warehouse state from semantic graph
        
        Process:
        1. Check for aisle occupancy conflicts (multiple agents want same aisle)
        2. Check for resource competition (same worker, forklift, equipment)
        3. Check for safety rule violations (forklift-worker proximity, aisle capacity)
        4. Check for SLA tradeoffs (multiple orders at risk, competing priorities)
        5. Group conflicting proposals into ConflictGroup objects
        
        Returns:
        - List of ConflictGroup objects, each representing a set of conflicting proposals
        
        Conflict Detection Logic:
        - Aisle Occupancy: If two proposals require same aisle in overlapping time windows
          and operations are incompatible (forklift + worker in narrow aisle), conflict detected
        - Resource Competition: If two proposals require same worker/forklift/equipment
          in overlapping time windows, conflict detected
        - Safety Violations: If proposal would violate safety rules (proximity, density,
          locks), conflict detected even if no other proposals exist
        - SLA Tradeoffs: If approving one proposal risks another order's SLA, conflict detected
        
        Edge Cases Handled:
        - Simultaneous proposals: If multiple agents submit proposals at same time for
          same resource, all are grouped into same ConflictGroup
        - Partial overlaps: If time windows overlap partially (e.g., 9:20-9:30 vs 9:25-9:35),
          conflict detected if resources cannot share
        - Cascading conflicts: If resolving one conflict creates another, all are tracked
          together in resolution logic
        """
        conflict_groups = []
        processed_proposals = set()  # Track which proposals have been assigned to conflict groups
        
        # Step 1: Check for aisle occupancy conflicts
        aisle_conflicts = self._detect_aisle_conflicts(proposals, global_state)
        for conflict in aisle_conflicts:
            conflict_groups.append(conflict)
            for proposal in conflict.conflicting_proposals:
                processed_proposals.add(id(proposal))
        
        # Step 2: Check for resource competition conflicts
        resource_conflicts = self._detect_resource_conflicts(proposals, global_state)
        for conflict in resource_conflicts:
            # Check if any proposals already in conflict group (merge if needed)
            existing_group = self._find_existing_conflict_group(conflict.conflicting_proposals, conflict_groups)
            if existing_group:
                # Merge conflicts (e.g., aisle conflict + resource conflict for same proposals)
                existing_group.conflicting_proposals.extend(
                    [p for p in conflict.conflicting_proposals if p not in existing_group.conflicting_proposals]
                )
                existing_group.conflict_type = "multi_dimensional"  # Multiple conflict types
            else:
                conflict_groups.append(conflict)
                for proposal in conflict.conflicting_proposals:
                    processed_proposals.add(id(proposal))
        
        # Step 3: Check for safety rule violations (even without other proposals)
        safety_conflicts = self._detect_safety_violations(proposals, global_state)
        for conflict in safety_conflicts:
            conflict_groups.append(conflict)
            for proposal in conflict.conflicting_proposals:
                processed_proposals.add(id(proposal))
        
        # Step 4: Check for SLA tradeoffs
        sla_conflicts = self._detect_sla_tradeoffs(proposals, global_state)
        for conflict in sla_conflicts:
            # Check if any proposals already in conflict group
            existing_group = self._find_existing_conflict_group(conflict.conflicting_proposals, conflict_groups)
            if existing_group:
                existing_group.conflicting_proposals.extend(
                    [p for p in conflict.conflicting_proposals if p not in existing_group.conflicting_proposals]
                )
            else:
                conflict_groups.append(conflict)
                for proposal in conflict.conflicting_proposals:
                    processed_proposals.add(id(proposal))
        
        return conflict_groups
    
    def score_and_rank(self, conflict_group: ConflictGroup, global_state: WarehouseState) -> List[Any]:
        """
        Uses priority, risk_score, uncertainty, and global rules to rank proposals.
        
        Inputs:
        - conflict_group: ConflictGroup containing conflicting proposals
        - global_state: Current warehouse state
        
        Process:
        1. Calculate composite score for each proposal:
           - Priority weight (Tier 1 > Tier 2 > Tier 3, Expedite > Standard)
           - Risk score (lower is better for approval)
           - Uncertainty (lower is better)
           - SLA urgency (time until promise date, cut-off time)
           - Operational impact (delay cost, throughput impact)
        2. Apply global rules:
           - Safety-first: Proposals violating safety rules get lowest priority
           - SLA priority: Orders with tighter deadlines get higher priority
           - Resource optimization: Proposals that minimize total delay get higher priority
        3. Sort proposals by composite score (highest first)
        
        Returns:
        - List of proposals sorted by priority (highest priority first)
        
        Scoring Formula (pseudocode):
        composite_score = (
            priority_weight * proposal.priority +
            sla_urgency_weight * sla_urgency_score +
            operational_impact_weight * (1 - operational_impact_score) -
            risk_penalty * proposal.risk_score -
            uncertainty_penalty * proposal.uncertainty
        )
        
        Where:
        - priority_weight: Higher for Tier 1, Expedite orders
        - sla_urgency_score: Higher for orders closer to promise date
        - operational_impact_score: Lower is better (less delay, less congestion)
        - risk_penalty: Higher risk reduces score
        - uncertainty_penalty: Higher uncertainty reduces score
        """
        proposals = conflict_group.conflicting_proposals
        scored_proposals = []
        
        for proposal in proposals:
            # Step 1: Calculate composite score components
            
            # Priority weight (from agent personalities: Tier 1 > Tier 2 > Tier 3)
            priority_weight = self._calculate_priority_weight(proposal, global_state)
            
            # SLA urgency (time until promise date, cut-off time)
            sla_urgency = self._calculate_sla_urgency(proposal, global_state)
            
            # Operational impact (delay cost, throughput impact)
            operational_impact = self._calculate_operational_impact(proposal, global_state)
            
            # Risk and uncertainty (lower is better)
            risk_penalty = proposal.risk_score  # From ProposedAction
            uncertainty_penalty = proposal.uncertainty  # From ProposedAction
            
            # Step 2: Apply global rules
            
            # Safety-first: If proposal violates safety, set score to minimum
            if self._violates_safety_rules(proposal, global_state):
                composite_score = -1000  # Minimum score, will be ranked last
            else:
                # Composite score calculation
                composite_score = (
                    priority_weight * 10.0 +  # Scale priority to 1-10 range
                    sla_urgency * 5.0 +
                    (1.0 - operational_impact) * 3.0 -  # Lower impact is better
                    risk_penalty * 2.0 -
                    uncertainty_penalty * 2.0
                )
            
            scored_proposals.append({
                'proposal': proposal,
                'score': composite_score,
                'priority_weight': priority_weight,
                'sla_urgency': sla_urgency,
                'operational_impact': operational_impact
            })
        
        # Step 3: Sort by composite score (highest first)
        scored_proposals.sort(key=lambda x: x['score'], reverse=True)
        
        # Return proposals in priority order
        return [item['proposal'] for item in scored_proposals]
    
    def apply_safety_and_SLA_rules(self, proposal: Any, global_state: WarehouseState) -> bool:
        """
        Returns whether this proposal is acceptable given safety and SLA rules.
        
        Inputs:
        - proposal: ProposedAction to evaluate
        - global_state: Current warehouse state
        
        Process:
        1. Check safety rules:
           - Aisle occupancy (only one forklift OR one worker in narrow aisle)
           - Forklift-worker proximity (minimum 10-foot clearance)
           - Worker density (max 3 workers per 100 sq ft in forward pick zones)
           - Aisle locks (no operations in locked aisles)
           - Equipment safety (equipment must be operational, certified workers only)
        2. Check SLA rules:
           - Order promise dates (cannot delay orders past promise date)
           - Priority tiers (Tier 1 > Tier 2 > Tier 3)
           - Cut-off times (cannot miss carrier cut-off times)
           - Expedite requests (expedite orders get priority)
        3. Return True if all rules satisfied, False otherwise
        
        Returns:
        - True if proposal passes all safety and SLA rules
        - False if proposal violates any rule
        
        Safety Rules (from architecture and personalities):
        - Aisle Occupancy: Narrow aisles (< 8 feet) can only accommodate one forklift
          OR one worker at a time. Wide aisles (> 8 feet) can accommodate multiple
          operations if clearance requirements met.
        - Forklift-Worker Proximity: Minimum 10-foot clearance required between
          forklift and worker paths. If proposal would create proximity < 10 feet,
          rule violated.
        - Worker Density: Maximum 3 workers per 100 sq ft in forward pick zones.
          If proposal increases density above threshold, rule violated.
        - Aisle Locks: If aisle is locked (maintenance, safety incident, planner override),
          no operations allowed. Proposal must be rejected or rescheduled.
        
        SLA Rules (from personalities):
        - Order Promise Dates: If proposal would delay order past promise date,
          rule violated (unless explicit planner override).
        - Priority Tiers: Tier 1 orders must not be delayed by Tier 2/3 orders.
          If proposal prioritizes lower tier over higher tier, rule violated.
        - Cut-off Times: If proposal would cause order to miss carrier cut-off,
          rule violated.
        - Expedite Requests: Expedite orders get priority over standard orders.
        """
        # Step 1: Safety rule checks
        
        # Check aisle occupancy
        if not self._check_aisle_occupancy(proposal, global_state):
            # Log: "Proposal {proposal_id} violates aisle occupancy rule"
            return False
        
        # Check forklift-worker proximity
        if not self._check_forklift_worker_proximity(proposal, global_state):
            # Log: "Proposal {proposal_id} violates forklift-worker proximity rule"
            return False
        
        # Check worker density
        if not self._check_worker_density(proposal, global_state):
            # Log: "Proposal {proposal_id} violates worker density rule"
            return False
        
        # Check aisle locks
        if not self._check_aisle_locks(proposal, global_state):
            # Log: "Proposal {proposal_id} violates aisle lock rule"
            return False
        
        # Check equipment safety
        if not self._check_equipment_safety(proposal, global_state):
            # Log: "Proposal {proposal_id} violates equipment safety rule"
            return False
        
        # Step 2: SLA rule checks
        
        # Check order promise dates
        if not self._check_order_promise_dates(proposal, global_state):
            # Log: "Proposal {proposal_id} violates order promise date rule"
            return False
        
        # Check priority tiers
        if not self._check_priority_tiers(proposal, global_state):
            # Log: "Proposal {proposal_id} violates priority tier rule"
            return False
        
        # Check cut-off times
        if not self._check_cutoff_times(proposal, global_state):
            # Log: "Proposal {proposal_id} violates cut-off time rule"
            return False
        
        # Check expedite requests
        if not self._check_expedite_requests(proposal, global_state):
            # Log: "Proposal {proposal_id} violates expedite request rule"
            return False
        
        # All rules passed
        return True
    
    def decide_resolution(self, conflict_group: ConflictGroup, global_state: WarehouseState) -> ResolutionDecision:
        """
        Encodes the Orchestrator's personality: safety-first, then SLA, then optimization.
        
        Inputs:
        - conflict_group: ConflictGroup containing conflicting proposals
        - global_state: Current warehouse state
        
        Process:
        1. Score and rank proposals by priority
        2. Apply safety-first rule: Reject any proposals that violate safety rules
        3. Apply SLA priority rule: Approve highest-priority proposals that don't violate safety
        4. Apply optimization rule: Reschedule lower-priority proposals to accommodate
           higher-priority ones, minimizing total delay
        5. Calculate risk scores and confidence for resolution
        6. Determine if escalation to HITL is required
        
        Returns:
        - ResolutionDecision object containing approved, rescheduled, and rejected proposals
        
        Orchestrator Personality (from agent_design/agent_personalities.md):
        - Safety-first: Never compromises on safety rules. Proposals violating safety
          are rejected immediately, regardless of priority or SLA pressure.
        - Balanced on SLA vs congestion: Can defer lower-priority work to protect
          high-priority orders, but also considers operational efficiency. Will reschedule
          routine operations to meet SLA commitments, but not at expense of creating
          severe congestion.
        - Defaults to HITL when tradeoffs are ambiguous: When multiple valid resolutions
          exist with different tradeoffs, or when resolution impacts multiple high-priority
          orders, escalates to planner rather than making autonomous decision.
        - Prefers deterministic, explainable choices: Uses explicit rules and data rather
          than probabilistic reasoning. Every resolution includes clear rationale.
        
        Resolution Algorithm:
        1. Rank proposals by composite score (from score_and_rank)
        2. For each proposal in priority order:
           a. If violates safety rules: REJECT
           b. If highest priority and doesn't violate safety: APPROVE
           c. If conflicts with approved proposal: RESCHEDULE (find alternative time/location)
           d. If rescheduling not possible: REJECT or ESCALATE
        3. Calculate resolution metrics (safety_risk, sla_risk, operational_impact)
        4. Determine if HITL required (using should_escalate_to_planner)
        """
        # Step 1: Score and rank proposals
        ranked_proposals = self.score_and_rank(conflict_group, global_state)
        
        # Step 2: Initialize resolution decision
        approved_proposals = []
        rescheduled_proposals = {}
        rejected_proposals = {}
        
        # Step 3: Apply safety-first rule - reject proposals violating safety
        for proposal in ranked_proposals:
            if not self.apply_safety_and_SLA_rules(proposal, global_state):
                # Safety or SLA violation - reject
                rejected_proposals[proposal.agent_name] = (
                    f"Proposal violates safety/SLA rules: "
                    f"{self._get_violation_details(proposal, global_state)}"
                )
        
        # Step 4: Apply SLA priority rule - approve highest-priority proposals
        for proposal in ranked_proposals:
            # Skip if already rejected
            if proposal.agent_name in rejected_proposals:
                continue
            
            # Check if proposal conflicts with already approved proposals
            conflicts_with_approved = False
            for approved in approved_proposals:
                if self._proposals_conflict(proposal, approved, global_state):
                    conflicts_with_approved = True
                    break
            
            if not conflicts_with_approved:
                # No conflict with approved proposals - approve
                approved_proposals.append(proposal)
            else:
                # Conflicts with approved proposal - try to reschedule
                alternative = self._find_alternative_time_or_location(proposal, global_state, approved_proposals)
                if alternative:
                    # Rescheduling possible
                    rescheduled_proposals[proposal.agent_name] = {
                        'new_time_window': alternative['time_window'],
                        'new_location': alternative.get('location'),
                        'reason': f"Rescheduled to accommodate higher-priority proposal from {approved.agent_name}"
                    }
                else:
                    # Rescheduling not possible - reject or escalate
                    if proposal.priority >= 8:  # High priority, escalate to HITL
                        # Will be handled by escalation logic
                        pass
                    else:
                        # Lower priority, reject
                        rejected_proposals[proposal.agent_name] = (
                            f"Cannot reschedule to accommodate higher-priority proposal, "
                            f"no alternative time/location available"
                        )
        
        # Step 5: Calculate resolution metrics
        safety_risk = self._calculate_resolution_safety_risk(approved_proposals, rescheduled_proposals, global_state)
        sla_risk = self._calculate_resolution_sla_risk(approved_proposals, rescheduled_proposals, global_state)
        operational_impact = self._calculate_resolution_operational_impact(approved_proposals, rescheduled_proposals, global_state)
        
        # Step 6: Calculate confidence
        confidence = self._calculate_resolution_confidence(
            approved_proposals, rescheduled_proposals, rejected_proposals,
            safety_risk, sla_risk, global_state
        )
        
        # Step 7: Build rationale
        rationale = self._build_resolution_rationale(
            conflict_group, approved_proposals, rescheduled_proposals,
            rejected_proposals, safety_risk, sla_risk, operational_impact
        )
        
        # Step 8: Create resolution decision
        resolution = ResolutionDecision(
            decision_id=f"resolution-{conflict_group.conflict_id}",
            conflict_group=conflict_group,
            approved_proposals=approved_proposals,
            rescheduled_proposals=rescheduled_proposals,
            rejected_proposals=rejected_proposals,
            escalation_required=False,  # Will be set by should_escalate_to_planner
            rationale=rationale,
            confidence=confidence,
            safety_risk=safety_risk,
            sla_risk=sla_risk,
            operational_impact=operational_impact
        )
        
        # Step 9: Check if escalation required
        resolution.escalation_required = self.should_escalate_to_planner(resolution)
        
        return resolution
    
    def route_for_HITL(self, decision: ResolutionDecision) -> PlannerDecisionRequest:
        """
        Builds the payload that will be shown to the planner in the UX flow.
        
        Inputs:
        - decision: ResolutionDecision that requires HITL review
        
        Process:
        1. Extract conflict information (agents, location, time window)
        2. Calculate risk indicators (safety, SLA, operational)
        3. Format proposals for display (agent name, action, priority, risk)
        4. Build orchestrator recommendation with rationale
        5. Calculate impact preview (SLA impact, congestion projection, operational metrics)
        6. Generate alternative resolutions (if any)
        7. Package into PlannerDecisionRequest
        
        Returns:
        - PlannerDecisionRequest object ready for UX display
        
        This structure is what the planner sees in the conflict resolution flow
        (see ux-flows/conflict_resolution_flow.md for UX details).
        
        The request includes:
        - Conflict summary (what, where, when, who)
        - Risk indicators (safety, SLA, operational)
        - Detailed proposal information
        - Orchestrator recommendation (what to approve, reschedule, reject)
        - Impact preview (what happens if recommendation approved)
        - Alternative resolutions (other valid options)
        - Confidence level (orchestrator's confidence in recommendation)
        """
        conflict = decision.conflict_group
        
        # Step 1: Extract conflict information
        agents_involved = [proposal.agent_name for proposal in conflict.conflicting_proposals]
        conflict_summary = (
            f"Conflict detected: {conflict.conflict_type} at {conflict.conflict_location} "
            f"during {conflict.conflict_time_window['earliest_start']} - "
            f"{conflict.conflict_time_window['latest_end']}. "
            f"Agents involved: {', '.join(agents_involved)}"
        )
        
        # Step 2: Calculate risk indicators
        risk_indicators = {
            'safety_risk': decision.safety_risk,
            'sla_risk': decision.sla_risk,
            'operational_impact': decision.operational_impact.get('delay_minutes', 0)
        }
        
        # Step 3: Format proposals for display
        formatted_proposals = []
        for proposal in conflict.conflicting_proposals:
            formatted_proposals.append({
                'agent_name': proposal.agent_name,
                'action_type': proposal.action_type,
                'target_entities': proposal.target_entities,
                'time_window': proposal.time_window,
                'priority': proposal.priority,
                'risk_score': proposal.risk_score,
                'uncertainty': proposal.uncertainty,
                'explanation': proposal.explanation,
                'confidence': proposal.confidence
            })
        
        # Step 4: Build orchestrator recommendation
        recommendation_summary = self._format_recommendation_summary(decision)
        
        # Step 5: Calculate impact preview
        impact_preview = self._calculate_impact_preview(decision, conflict)
        
        # Step 6: Generate alternative resolutions
        alternatives = self._generate_alternative_resolutions(decision, conflict)
        
        # Step 7: Package into PlannerDecisionRequest
        hitl_request = PlannerDecisionRequest(
            request_id=f"hitl-{decision.decision_id}",
            conflict_summary=conflict_summary,
            agents_involved=agents_involved,
            location=conflict.conflict_location,
            time_window=conflict.conflict_time_window,
            risk_indicators=risk_indicators,
            proposals=formatted_proposals,
            orchestrator_recommendation=decision,
            impact_preview=impact_preview,
            alternatives=alternatives,
            confidence=decision.confidence,
            detected_at=conflict.detected_at
        )
        
        return hitl_request
    
    def finalize_actions(self, decisions: List[ResolutionDecision]) -> List[ApprovedAction]:
        """
        Returns the list of actions to send to underlying deterministic engines.
        
        Inputs:
        - decisions: List of ResolutionDecision objects (approved by orchestrator or planner)
        
        Process:
        1. Extract approved proposals from each decision
        2. Extract rescheduled proposals and update their time windows/locations
        3. Convert proposals to ApprovedAction objects
        4. Set execution priority based on original proposal priority
        5. Mark safety and SLA validation status
        6. Record approval source (orchestrator auto-approval or planner approval)
        
        Returns:
        - List of ApprovedAction objects ready for execution
        
        These ApprovedAction objects are what get sent to deterministic execution
        engines (constraint solvers, optimization engines) that actually execute
        the physical warehouse operations.
        """
        approved_actions = []
        
        for decision in decisions:
            # Step 1: Process approved proposals
            for proposal in decision.approved_proposals:
                approved_action = ApprovedAction(
                    action_id=f"action-{proposal.agent_name}-{decision.decision_id}",
                    original_proposal=proposal,
                    approved_time_window=proposal.time_window,
                    approved_resources=proposal.required_resources,
                    execution_priority=proposal.priority,
                    safety_validated=True,  # Already validated in decide_resolution
                    sla_validated=True,  # Already validated in decide_resolution
                    approved_by="orchestrator" if not decision.escalation_required else "planner:pending",
                    approved_at=datetime.now()
                )
                approved_actions.append(approved_action)
            
            # Step 2: Process rescheduled proposals
            for agent_name, reschedule_info in decision.rescheduled_proposals.items():
                # Find original proposal
                original_proposal = next(
                    (p for p in decision.conflict_group.conflicting_proposals if p.agent_name == agent_name),
                    None
                )
                if original_proposal:
                    approved_action = ApprovedAction(
                        action_id=f"action-{agent_name}-{decision.decision_id}-rescheduled",
                        original_proposal=original_proposal,
                        approved_time_window=reschedule_info['new_time_window'],
                        approved_resources=original_proposal.required_resources,
                        execution_priority=original_proposal.priority,
                        safety_validated=True,
                        sla_validated=True,
                        approved_by="orchestrator" if not decision.escalation_required else "planner:pending",
                        approved_at=datetime.now()
                    )
                    approved_actions.append(approved_action)
        
        return approved_actions
    
    def should_escalate_to_planner(self, decision: ResolutionDecision) -> bool:
        """
        Encodes escalation rules based on risk, uncertainty, and impact.
        
        Inputs:
        - decision: ResolutionDecision to evaluate for escalation
        
        Process:
        Evaluates escalation criteria from Orchestrator personality:
        1. Risk score exceeds threshold (safety_risk > 0.1, sla_risk > 0.2)
        2. Confidence below threshold (< 0.95)
        3. Complexity exceeds threshold (> 2 agents in conflict)
        4. Impact on critical SLAs (multiple orders at risk, high-priority orders affected)
        5. Presence of safety overrides or policy exceptions
        6. Ambiguous tradeoffs (multiple valid resolutions with different impacts)
        
        Returns:
        - True if escalation to planner (HITL) required
        - False if auto-approval acceptable
        
        Escalation Rules (from agent_design/agent_personalities.md):
        - Escalates when:
          * Risk level exceeds threshold: safety_risk > 0.1, sla_risk > 0.2,
            or operational_impact > 30 minutes delay
          * SLAs are at risk and tradeoffs exist: Multiple orders at risk, or
            high-priority order requires delaying other operations
          * Data is incomplete or conflicting: Semantic graph shows conflicting state,
            sensor anomalies detected, or proposal metadata missing
          * Complexity exceeds threshold: More than 2 agents in conflict, or resolution
            requires coordination across 3+ domains
          * Planner override exists: Manual locks, explicit priorities, or previous
            planner decisions conflict with proposed resolution
        """
        # Rule 1: Risk score exceeds threshold
        if decision.safety_risk > self.safety_risk_threshold:
            return True  # Safety risk too high, require human review
        
        if decision.sla_risk > self.sla_risk_threshold:
            return True  # SLA risk too high, require human review
        
        # Rule 2: Confidence below threshold
        if decision.confidence < self.confidence_threshold:
            return True  # Low confidence, require human judgment
        
        # Rule 3: Complexity exceeds threshold
        num_agents = len(decision.conflict_group.conflicting_proposals)
        if num_agents > self.complexity_threshold:
            return True  # Too many agents, require human coordination
        
        # Rule 4: Impact on critical SLAs
        if self._has_critical_sla_impact(decision):
            return True  # Critical SLAs at risk, require human judgment
        
        # Rule 5: Safety overrides or policy exceptions
        if self._has_safety_overrides(decision):
            return True  # Safety overrides present, require human review
        
        # Rule 6: Ambiguous tradeoffs
        if self._has_ambiguous_tradeoffs(decision):
            return True  # Multiple valid resolutions, require human choice
        
        # All criteria passed - auto-approval acceptable
        return False
    
    # ============================================================================
    # Helper Methods (Placeholder Implementations)
    # ============================================================================
    
    def _validate_proposal_schema(self, proposal: Any) -> bool:
        """Validate proposal has all required fields."""
        # In production: Check against JSON schema
        required_fields = ['agent_name', 'action_type', 'time_window', 'priority', 'risk_score', 'uncertainty']
        return all(hasattr(proposal, field) for field in required_fields)
    
    def _is_proposal_stale(self, proposal: Any, current_time: datetime) -> bool:
        """Check if proposal's time window has expired or state changed significantly."""
        # In production: Compare proposal timestamp with current state timestamp
        # Also check if time window has passed
        if proposal.time_window['latest_end'] < current_time:
            return True  # Time window expired
        # Could also check if global state changed significantly since proposal generated
        return False
    
    def _has_complete_metadata(self, proposal: Any) -> bool:
        """Check if proposal has all required metadata."""
        # In production: Validate confidence, risk_score, uncertainty, explanation present
        return (
            hasattr(proposal, 'confidence') and proposal.confidence is not None and
            hasattr(proposal, 'risk_score') and proposal.risk_score is not None and
            hasattr(proposal, 'uncertainty') and proposal.uncertainty is not None
        )
    
    def _is_duplicate_proposal(self, proposal: Any) -> bool:
        """Check if proposal is duplicate of existing active proposal."""
        # In production: Compare agent_name, action_type, target_entities, time_window
        for active in self.active_proposals:
            if (active.agent_name == proposal.agent_name and
                active.action_type == proposal.action_type and
                active.target_entities == proposal.target_entities):
                return True
        return False
    
    def _remove_duplicate(self, proposal: Any):
        """Remove older duplicate proposal from active list."""
        # In production: Remove older duplicate, keep newer one
        self.active_proposals = [
            p for p in self.active_proposals
            if not (p.agent_name == proposal.agent_name and
                   p.action_type == proposal.action_type and
                   p.target_entities == proposal.target_entities)
        ]
    
    def _passes_basic_constraints(self, proposal: Any) -> bool:
        """Check if proposal passes basic constraints (locks, maintenance windows)."""
        # In production: Query semantic graph for aisle locks, maintenance windows
        # Check if proposal's location/aisle is locked or in maintenance
        return True  # Placeholder
    
    def _detect_aisle_conflicts(self, proposals: List[Any], global_state: WarehouseState) -> List[ConflictGroup]:
        """Detect conflicts where multiple proposals require same aisle."""
        conflicts = []
        # In production: Group proposals by aisle, check for overlapping time windows
        # Check if operations are incompatible (forklift + worker in narrow aisle)
        return conflicts
    
    def _detect_resource_conflicts(self, proposals: List[Any], global_state: WarehouseState) -> List[ConflictGroup]:
        """Detect conflicts where multiple proposals require same resources."""
        conflicts = []
        # In production: Group proposals by required resources (worker, forklift, equipment)
        # Check for overlapping time windows
        return conflicts
    
    def _detect_safety_violations(self, proposals: List[Any], global_state: WarehouseState) -> List[ConflictGroup]:
        """Detect proposals that violate safety rules even without other proposals."""
        conflicts = []
        # In production: Check each proposal against safety rules
        # If violation detected, create ConflictGroup with single proposal
        return conflicts
    
    def _detect_sla_tradeoffs(self, proposals: List[Any], global_state: WarehouseState) -> List[ConflictGroup]:
        """Detect conflicts where approving one proposal risks another's SLA."""
        conflicts = []
        # In production: Check if approving proposal A would delay proposal B past promise date
        return conflicts
    
    def _find_existing_conflict_group(self, proposals: List[Any], conflict_groups: List[ConflictGroup]) -> Optional[ConflictGroup]:
        """Find if any proposals already belong to existing conflict group."""
        # In production: Check if any proposal in proposals list is already in conflict_groups
        return None
    
    def _calculate_priority_weight(self, proposal: Any, global_state: WarehouseState) -> float:
        """Calculate priority weight for proposal (Tier 1 > Tier 2 > Tier 3)."""
        # In production: Extract priority tier from proposal, map to weight
        # Tier 1: 1.0, Tier 2: 0.7, Tier 3: 0.4
        return proposal.priority / 10.0  # Normalize 1-10 scale
    
    def _calculate_sla_urgency(self, proposal: Any, global_state: WarehouseState) -> float:
        """Calculate SLA urgency score (higher for orders closer to promise date)."""
        # In production: Extract order promise date, calculate time remaining
        # Higher urgency for shorter time remaining
        return 0.5  # Placeholder
    
    def _calculate_operational_impact(self, proposal: Any, global_state: WarehouseState) -> float:
        """Calculate operational impact score (delay, congestion, throughput)."""
        # In production: Estimate delay minutes, congestion increase, throughput impact
        return 0.3  # Placeholder
    
    def _violates_safety_rules(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check if proposal violates safety rules."""
        return not self.apply_safety_and_SLA_rules(proposal, global_state)
    
    def _check_aisle_occupancy(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check aisle occupancy rule."""
        # In production: Query semantic graph for aisle occupancy in proposal time window
        # Check if narrow aisle (< 8 feet) and incompatible operations
        return True  # Placeholder
    
    def _check_forklift_worker_proximity(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check forklift-worker proximity rule (minimum 10-foot clearance)."""
        # In production: Calculate distance between forklift and worker paths
        # Return False if distance < 10 feet
        return True  # Placeholder
    
    def _check_worker_density(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check worker density rule (max 3 workers per 100 sq ft)."""
        # In production: Calculate worker density in zone after proposal
        # Return False if density > 3.0
        return True  # Placeholder
    
    def _check_aisle_locks(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check if proposal's aisle is locked."""
        # In production: Query semantic graph for aisle lock status
        # Return False if aisle locked
        return True  # Placeholder
    
    def _check_equipment_safety(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check equipment safety (operational, certified workers)."""
        # In production: Check equipment status, worker certifications
        return True  # Placeholder
    
    def _check_order_promise_dates(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check if proposal would delay order past promise date."""
        # In production: Extract order promise date, calculate if proposal would delay
        return True  # Placeholder
    
    def _check_priority_tiers(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check if proposal prioritizes lower tier over higher tier."""
        # In production: Compare proposal priority with other active proposals
        return True  # Placeholder
    
    def _check_cutoff_times(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check if proposal would cause order to miss carrier cut-off."""
        # In production: Extract carrier cut-off time, calculate if proposal would miss
        return True  # Placeholder
    
    def _check_expedite_requests(self, proposal: Any, global_state: WarehouseState) -> bool:
        """Check if proposal respects expedite request priority."""
        # In production: Check if proposal delays expedite orders
        return True  # Placeholder
    
    def _get_violation_details(self, proposal: Any, global_state: WarehouseState) -> str:
        """Get details of safety/SLA violations."""
        # In production: Identify which specific rules were violated
        return "Safety/SLA violation details"
    
    def _proposals_conflict(self, proposal1: Any, proposal2: Any, global_state: WarehouseState) -> bool:
        """Check if two proposals conflict."""
        # In production: Check if proposals require same resources in overlapping time windows
        return False  # Placeholder
    
    def _find_alternative_time_or_location(self, proposal: Any, global_state: WarehouseState, approved_proposals: List[Any]) -> Optional[Dict[str, Any]]:
        """Find alternative time window or location for proposal."""
        # In production: Query semantic graph for available time windows/locations
        # Check if alternative doesn't conflict with approved proposals
        return None  # Placeholder
    
    def _calculate_resolution_safety_risk(self, approved: List[Any], rescheduled: Dict, global_state: WarehouseState) -> float:
        """Calculate safety risk after resolution."""
        # In production: Evaluate safety risk of approved + rescheduled proposals
        return 0.05  # Placeholder
    
    def _calculate_resolution_sla_risk(self, approved: List[Any], rescheduled: Dict, global_state: WarehouseState) -> float:
        """Calculate SLA risk after resolution."""
        # In production: Evaluate SLA risk of approved + rescheduled proposals
        return 0.1  # Placeholder
    
    def _calculate_resolution_operational_impact(self, approved: List[Any], rescheduled: Dict, global_state: WarehouseState) -> Dict[str, Any]:
        """Calculate operational impact after resolution."""
        # In production: Calculate delay minutes, throughput impact, congestion
        return {'delay_minutes': 15, 'throughput_impact': 0.02}  # Placeholder
    
    def _calculate_resolution_confidence(self, approved: List[Any], rescheduled: Dict, rejected: Dict, safety_risk: float, sla_risk: float, global_state: WarehouseState) -> float:
        """Calculate confidence in resolution."""
        # In production: Combine proposal confidence scores, risk scores, data completeness
        return 0.92  # Placeholder
    
    def _build_resolution_rationale(self, conflict: ConflictGroup, approved: List[Any], rescheduled: Dict, rejected: Dict, safety_risk: float, sla_risk: float, operational_impact: Dict) -> str:
        """Build explanation of resolution."""
        # In production: Generate structured explanation
        return (
            f"Resolution for {conflict.conflict_type} at {conflict.conflict_location}: "
            f"Approved {len(approved)} proposals, rescheduled {len(rescheduled)} proposals, "
            f"rejected {len(rejected)} proposals. Safety risk: {safety_risk:.2f}, "
            f"SLA risk: {sla_risk:.2f}, Operational impact: {operational_impact.get('delay_minutes', 0)} minutes."
        )
    
    def _has_critical_sla_impact(self, decision: ResolutionDecision) -> bool:
        """Check if resolution impacts critical SLAs."""
        # In production: Check if multiple orders at risk or high-priority orders affected
        return False  # Placeholder
    
    def _has_safety_overrides(self, decision: ResolutionDecision) -> bool:
        """Check if safety overrides or policy exceptions present."""
        # In production: Check for planner overrides, manual locks, policy exceptions
        return False  # Placeholder
    
    def _has_ambiguous_tradeoffs(self, decision: ResolutionDecision) -> bool:
        """Check if multiple valid resolutions exist with different tradeoffs."""
        # In production: Evaluate if alternative resolutions have similar scores but different impacts
        return False  # Placeholder
    
    def _format_recommendation_summary(self, decision: ResolutionDecision) -> str:
        """Format orchestrator recommendation for display."""
        # In production: Generate structured recommendation text
        return decision.rationale
    
    def _calculate_impact_preview(self, decision: ResolutionDecision, conflict: ConflictGroup) -> Dict[str, Any]:
        """Calculate impact preview for HITL request."""
        # In production: Calculate SLA impact, congestion projection, operational metrics
        return {
            'sla_impact': 'Low',
            'congestion_projection': 'Moderate',
            'operational_metrics': decision.operational_impact
        }
    
    def _generate_alternative_resolutions(self, decision: ResolutionDecision, conflict: ConflictGroup) -> List[Dict[str, Any]]:
        """Generate alternative resolutions for HITL request."""
        # In production: Generate alternative resolutions with different tradeoffs
        return []  # Placeholder


# ============================================================================
# Example Scenario: Slotting vs Replenishment Conflict
# ============================================================================

"""
Example Walkthrough: SlottingAgent and ReplenishmentAgent Conflict

Scenario:
---------
- SlottingAgent proposes moving Item X from reserve Location R-45 to forward pick
  Location A-12-08 at 9:25-9:40 AM to optimize pick efficiency (67% travel time reduction).
- ReplenishmentAgent proposes replenishing Location A-12-05 (adjacent location, same aisle)
  from reserve at 9:20-9:35 AM to prevent stockout (15 units remaining, reorder point: 20).
- Both operations require forklift access to Aisle A-12, but narrow aisle (8 feet) can
  only accommodate one forklift at a time.
- PickingAgent has 3 high-priority orders scheduled to pick from Aisle A-12 between
  9:20-9:50 AM, requiring worker access.

Step-by-Step Orchestrator Behavior:
------------------------------------

1. collect_proposals():
   - Receives proposals from SlottingAgent and ReplenishmentAgent
   - Validates schema: Both proposals have required fields (agent_name, action_type, etc.)
   - Checks staleness: Time windows are in future, state is current
   - Validates metadata: Both have confidence scores, risk scores, explanations
   - No duplicates detected
   - Basic constraints: Aisle A-12 not locked, no maintenance windows
   - Both proposals added to active_proposals list

2. detect_conflicts():
   - Queries semantic graph for Aisle A-12 occupancy in time windows 9:20-9:50 AM
   - Detects aisle occupancy conflict:
     * SlottingAgent: Forklift 3, Aisle A-12, 9:25-9:40 AM
     * ReplenishmentAgent: Forklift 5, Aisle A-12, 9:20-9:35 AM
     * Time windows overlap (9:25-9:35 AM)
     * Narrow aisle cannot accommodate two forklifts simultaneously
   - Creates ConflictGroup:
     * conflict_type: "aisle_occupancy"
     * conflict_location: "Aisle A-12"
     * conflict_time_window: {earliest_start: 9:20 AM, latest_end: 9:40 AM}
     * conflicting_proposals: [SlottingAgent proposal, ReplenishmentAgent proposal]
     * risk_score: 0.15 (medium risk due to stockout potential and operational impact)

3. score_and_rank():
   - ReplenishmentAgent proposal:
     * Priority: 7 (routine replenishment, but stockout risk)
     * SLA urgency: 0.6 (stockout in 2 hours, 3 high-priority orders require location)
     * Operational impact: 0.2 (minor delay acceptable)
     * Risk score: 0.3 (medium risk due to conflicts)
     * Uncertainty: 0.12 (high confidence in stockout risk)
     * Composite score: 7.0 * 10 + 0.6 * 5 + (1-0.2) * 3 - 0.3 * 2 - 0.12 * 2 = 76.36
   - SlottingAgent proposal:
     * Priority: 5 (optimization, not time-critical)
     * SLA urgency: 0.2 (long-term efficiency improvement, not immediate SLA impact)
     * Operational impact: 0.3 (20-minute aisle access, may delay picks)
     * Risk score: 0.2 (low risk, but congestion concern)
     * Uncertainty: 0.10 (high confidence in slotting benefit)
     * Composite score: 5.0 * 10 + 0.2 * 5 + (1-0.3) * 3 - 0.2 * 2 - 0.10 * 2 = 52.1
   - Ranked order: [ReplenishmentAgent, SlottingAgent] (higher score first)

4. apply_safety_and_SLA_rules():
   - ReplenishmentAgent proposal:
     * Aisle occupancy: Pass (no current occupancy, but conflicts with SlottingAgent)
     * Forklift-worker proximity: Pass (no workers in aisle during proposed time)
     * Worker density: Pass (no density increase)
     * Aisle locks: Pass (aisle not locked)
     * Order promise dates: Pass (no orders delayed)
     * Priority tiers: Pass (routine operation, doesn't violate tiers)
     * Result: PASS (but conflicts with SlottingAgent)
   - SlottingAgent proposal:
     * Same checks: PASS (but conflicts with ReplenishmentAgent)

5. decide_resolution():
   - Applies safety-first rule: Both proposals pass safety checks
   - Applies SLA priority rule:
     * ReplenishmentAgent: Higher priority (stockout prevention), APPROVE
     * SlottingAgent: Lower priority (optimization), conflicts with approved, RESCHEDULE
   - Finds alternative for SlottingAgent:
     * Queries semantic graph for available time windows after 9:35 AM
     * Finds window: 9:50-10:05 AM (after ReplenishmentAgent completes, after picking completes)
     * Alternative location: None needed (same location, different time)
   - Resolution:
     * approved_proposals: [ReplenishmentAgent proposal]
     * rescheduled_proposals: {SlottingAgent: {new_time_window: 9:50-10:05 AM, reason: "Rescheduled to accommodate ReplenishmentAgent"}}
     * rejected_proposals: {}
     * safety_risk: 0.05 (low, no safety violations)
     * sla_risk: 0.1 (low, stockout prevented, slotting delay acceptable)
     * operational_impact: {delay_minutes: 25, throughput_impact: 0.01}
     * confidence: 0.92 (high confidence in resolution)
     * rationale: "ReplenishmentAgent approved to prevent stockout (15 units remaining, 3 high-priority orders require location). SlottingAgent rescheduled to 9:50-10:05 AM to avoid conflict. Safety risk: 0.05, SLA risk: 0.1, operational impact: 25-minute delay for optimization (acceptable)."

6. should_escalate_to_planner():
   - Safety risk: 0.05 < 0.1 threshold → No escalation
   - SLA risk: 0.1 < 0.2 threshold → No escalation
   - Confidence: 0.92 < 0.95 threshold → ESCALATION REQUIRED
   - Complexity: 2 agents = 2, not > 2 threshold → No escalation
   - Critical SLA impact: No → No escalation
   - Safety overrides: No → No escalation
   - Ambiguous tradeoffs: No → No escalation
   - Result: ESCALATE (due to confidence < 0.95)

7. route_for_HITL():
   - Builds PlannerDecisionRequest:
     * conflict_summary: "Conflict detected: aisle_occupancy at Aisle A-12 during 9:20 AM - 9:40 AM. Agents involved: ReplenishmentAgent, SlottingAgent"
     * risk_indicators: {safety_risk: 0.05, sla_risk: 0.1, operational_impact: 25}
     * orchestrator_recommendation: ResolutionDecision from step 5
     * impact_preview: {sla_impact: 'Low', congestion_projection: 'Moderate', operational_metrics: {delay_minutes: 25}}
     * confidence: 0.92
   - Planner sees HITL card in UX flow with:
     * Conflict summary
     * Two proposals (ReplenishmentAgent, SlottingAgent)
     * Orchestrator recommendation: Approve Replenishment, Reschedule Slotting
     * Impact preview: 25-minute delay for optimization, no SLA impact
     * Action buttons: Approve, Reject, Modify, More Info

8. Planner Decision:
   - Planner reviews HITL card, sees recommendation makes sense:
     * Replenishment prevents stockout (critical)
     * Slotting optimization can wait 25 minutes (acceptable)
     * No safety or SLA risks
   - Planner clicks "Approve Recommendation"

9. finalize_actions():
   - Creates ApprovedAction for ReplenishmentAgent:
     * approved_time_window: 9:20-9:35 AM (original)
     * execution_priority: 7
     * approved_by: "planner:sarah_johnson"
   - Creates ApprovedAction for SlottingAgent (rescheduled):
     * approved_time_window: 9:50-10:05 AM (rescheduled)
     * execution_priority: 5
     * approved_by: "planner:sarah_johnson"
   - Both actions sent to deterministic execution engines

Result:
-------
- ReplenishmentAgent proceeds at 9:20-9:35 AM, prevents stockout
- SlottingAgent rescheduled to 9:50-10:05 AM, optimization delayed but acceptable
- No safety violations, no SLA violations, minimal operational impact
- Planner saw HITL card due to confidence < 0.95 threshold, approved recommendation
"""

