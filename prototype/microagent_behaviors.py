"""
Micro-Agent Behavior Specifications for Hybrid Agentic WMS

This file contains PSEUDOCODE behavior specifications for micro-agents in the
Warehouse Management System. This is NOT production-ready code, but rather a
behavioral specification that engineers can use to implement agent logic.

Purpose:
--------
- Define how each micro-agent thinks before proposing actions
- Encode agent personalities: objectives, risk posture, escalation behavior
- Produce structured proposals that the WMS Orchestrator can evaluate for conflicts
- Serve as a bridge between personality specifications and implementation

Connections to Other Documents:
--------------------------------
- architecture/wms_hybrid_architecture.md
  Defines the hybrid orchestrator + micro-agent architecture, semantic warehouse
  graph, deterministic engines, and conflict resolution patterns. This file
  implements the micro-agent proposal generation layer.

- ux-flows/conflict_resolution_flow.md
  Defines how conflicts are detected, resolved, and presented to planners.
  This file generates the proposals that trigger conflict detection.

- agent_design/agent_personalities.md
  Defines operating personas for each agent: objectives, risk posture,
  escalation triggers, explanation style. This file encodes those personalities
  into behavioral logic.

How Engineers Can Use This:
---------------------------
1. Use ProposedAction schema as contract for agent-orchestrator communication
2. Implement each agent's propose_actions() method following the pseudocode logic
3. Extend WarehouseContext to include additional data sources as needed
4. Refine constraint checking, risk calculation, and escalation logic based on
   production learnings
5. Add unit tests that verify agents generate proposals consistent with
   personality specifications

Notes:
------
- All agents inherit the global archetype: "Warehouse Control Tower Partner"
- Agents must respect non-negotiable constraints and escalate uncertainty
- Proposals must be evidence-based, with clear explanations and confidence levels
- Agents never proceed autonomously when safety constraints cannot be satisfied
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


# ============================================================================
# Shared Data Structures
# ============================================================================

@dataclass
class ProposedAction:
    """
    Schema for agent proposals sent to WMS Orchestrator.
    
    All micro-agents must generate proposals in this format to enable
    consistent conflict detection and resolution by the orchestrator.
    """
    agent_name: str                    # e.g., "SlottingAgent", "PickingAgent"
    action_type: str                   # e.g., "slotting_move", "pick_assignment", "replenishment"
    target_entities: Dict[str, Any]    # locations, SKUs, orders, workers, doors, etc.
    time_window: Dict[str, datetime]   # earliest_start, latest_end
    required_resources: List[str]       # forklifts, workers, doors, equipment IDs
    priority: int                       # higher = more urgent (1-10 scale, 10 = critical)
    risk_score: float                  # 0.0-1.0, derived from agent's personality and checks
    uncertainty: float                 # 0.0-1.0, how unsure the agent is (0.0 = certain)
    constraints_respected: List[str]    # list of constraints explicitly checked
    potential_conflicts: List[str]      # what it suspects may conflict (aisle, bin, door, etc.)
    explanation: str                    # short natural language rationale
    confidence: float                   # 0.0-1.0, agent's confidence in proposal
    alternatives: List[Dict[str, Any]]  # alternative actions considered (if any)
    data_sources: List[str]             # semantic graph queries, sensor data, etc. used


class WarehouseContext:
    """
    Placeholder for warehouse state that agents can inspect.
    
    In production, this would be implemented as queries to:
    - Semantic Warehouse Graph (entities, relationships, constraints)
    - Real-time sensor data (aisle occupancy, location status)
    - Historical patterns (pick frequency, congestion metrics)
    - Active operations (current tasks, scheduled operations)
    - Labor state (worker availability, skills, capacity, fatigue)
    - Safety flags (aisle locks, maintenance windows, incidents)
    """
    # Inventory state
    inventory_at_location: Dict[str, int]  # location_id -> quantity
    location_capacity: Dict[str, int]      # location_id -> max_capacity
    location_status: Dict[str, str]        # location_id -> "available" | "locked" | "maintenance"
    
    # Order state
    active_orders: List[Dict[str, Any]]    # order_id, promise_date, priority, items
    order_items: Dict[str, List[str]]      # order_id -> list of (sku, location, quantity)
    
    # Labor state
    worker_availability: Dict[str, bool]   # worker_id -> available
    worker_skills: Dict[str, List[str]]    # worker_id -> list of skills
    worker_capacity: Dict[str, int]        # worker_id -> remaining_capacity_minutes
    worker_location: Dict[str, str]        # worker_id -> current_zone
    
    # Equipment state
    forklift_availability: Dict[str, bool]  # forklift_id -> available
    equipment_status: Dict[str, str]        # equipment_id -> "operational" | "maintenance"
    
    # Aisle/zone state
    aisle_occupancy: Dict[str, str]        # aisle_id -> "empty" | "occupied" | "locked"
    aisle_capacity: Dict[str, int]         # aisle_id -> max_concurrent_operations
    worker_density: Dict[str, float]       # zone_id -> workers_per_100sqft
    
    # Safety state
    safety_locks: List[str]                # list of locked aisle/location IDs
    maintenance_windows: Dict[str, tuple]  # location_id -> (start_time, end_time)
    
    # Congestion metrics
    congestion_by_zone: Dict[str, float]  # zone_id -> congestion_score (0.0-1.0)
    historical_congestion: Dict[str, List[float]]  # zone_id -> list of historical scores
    
    # Time context
    current_time: datetime
    peak_hours: List[tuple]                # list of (start_hour, end_hour) tuples


# ============================================================================
# Slotting Agent
# ============================================================================

class SlottingAgent:
    """
    Personality: Optimizes storage location assignments to minimize travel time
    for picking operations. Prefers forward pick optimization, incremental
    movements, off-peak scheduling. Low risk tolerance for congestion.
    
    Key traits:
    - Prefers proactive optimization over reactive fixes
    - Requires 0.90+ confidence before proposing movement
    - Escalates when slotting conflicts with high-priority picking
    - Always checks aisle capacity, compatibility rules, congestion
    """
    
    def propose_actions(self, context: WarehouseContext) -> List[ProposedAction]:
        """
        Generate slotting proposals based on storage optimization opportunities.
        
        Logic:
        1. Identify items that should move (slow-moving from forward pick to reserve,
           fast-moving from reserve to forward pick)
        2. Evaluate each potential movement against constraints
        3. Calculate benefit (travel time reduction, pick efficiency improvement)
        4. Only propose if confidence >= 0.90 and benefit is significant
        5. Escalate if conflicts with high-priority operations
        """
        proposals = []
        
        # Step 1: Identify optimization opportunities
        # In production: Query semantic graph for items with suboptimal locations
        # based on pick frequency, travel time, space utilization
        optimization_opportunities = self._identify_slotting_opportunities(context)
        
        for opportunity in optimization_opportunities:
            item_sku = opportunity['sku']
            current_location = opportunity['current_location']
            proposed_location = opportunity['proposed_location']
            expected_benefit = opportunity['travel_time_reduction_percent']
            
            # Step 2: Check non-negotiable constraints
            constraints_checked = []
            can_proceed = True
            
            # Constraint: Aisle capacity and congestion
            aisle_id = self._get_aisle_from_location(proposed_location)
            if context.aisle_occupancy.get(aisle_id) == "locked":
                # Never propose movements to locked aisles
                continue
            if context.congestion_by_zone.get(aisle_id, 0.0) > 0.7:
                # Low risk tolerance for congestion - defer if high congestion
                continue
            constraints_checked.append("aisle_capacity")
            constraints_checked.append("congestion_threshold")
            
            # Constraint: Location compatibility (temperature, hazardous, size/weight)
            if not self._check_location_compatibility(item_sku, proposed_location, context):
                continue
            constraints_checked.append("location_compatibility")
            
            # Constraint: Space availability
            if context.inventory_at_location.get(proposed_location, 0) >= \
               context.location_capacity.get(proposed_location, 0):
                continue
            constraints_checked.append("space_capacity")
            
            # Constraint: Not during peak picking if alternative exists
            proposed_time = self._calculate_optimal_time_window(context, aisle_id)
            if self._is_peak_picking_hours(context, proposed_time) and \
               self._has_off_peak_alternative(context, aisle_id):
                # Prefer off-peak scheduling
                proposed_time = self._find_off_peak_window(context, aisle_id)
            constraints_checked.append("peak_hours_avoidance")
            
            # Step 3: Check for conflicts with active operations
            potential_conflicts = []
            if self._has_active_picking_in_aisle(context, aisle_id, proposed_time):
                potential_conflicts.append(f"active_picking_in_aisle_{aisle_id}")
                # Escalate if conflicts with high-priority picking
                if self._has_high_priority_picking(context, aisle_id, proposed_time):
                    # Don't propose - escalate instead
                    self._escalate_to_orchestrator(
                        f"Slotting opportunity conflicts with high-priority picking in {aisle_id}"
                    )
                    continue
            
            # Step 4: Calculate risk and uncertainty
            risk_score = self._calculate_slotting_risk(
                context, aisle_id, proposed_time, potential_conflicts
            )
            uncertainty = self._calculate_slotting_uncertainty(
                context, item_sku, current_location, proposed_location
            )
            confidence = 1.0 - uncertainty
            
            # Step 5: Only propose if confidence >= 0.90 (personality requirement)
            if confidence < 0.90:
                # Escalate uncertainty instead of proposing
                self._escalate_uncertainty(
                    f"Slotting benefit uncertain for {item_sku}: confidence {confidence:.2f}"
                )
                continue
            
            # Step 6: Only propose if benefit is significant (> 5% travel time reduction)
            if expected_benefit < 0.05:
                continue
            
            # Step 7: Generate proposal
            proposal = ProposedAction(
                agent_name="SlottingAgent",
                action_type="slotting_move",
                target_entities={
                    "sku": item_sku,
                    "from_location": current_location,
                    "to_location": proposed_location,
                    "aisle": aisle_id
                },
                time_window={
                    "earliest_start": proposed_time['start'],
                    "latest_end": proposed_time['end']
                },
                required_resources=["forklift"],  # Slotting requires forklift
                priority=self._calculate_slotting_priority(expected_benefit, context),
                risk_score=risk_score,
                uncertainty=uncertainty,
                constraints_respected=constraints_checked,
                potential_conflicts=potential_conflicts,
                explanation=(
                    f"Move {item_sku} from {current_location} to {proposed_location} "
                    f"to reduce pick travel time by {expected_benefit:.1%}. "
                    f"Historical data: {item_sku} picked {opportunity['pick_frequency']}x/day, "
                    f"forward pick locations have 30% faster average pick times. "
                    f"Movement requires 20-minute aisle access, may delay 2 low-priority picks "
                    f"if scheduled during peak hours."
                ),
                confidence=confidence,
                alternatives=self._generate_slotting_alternatives(context, opportunity),
                data_sources=[
                    "semantic_graph:item_pick_frequency",
                    "semantic_graph:location_travel_time",
                    "historical:congestion_patterns"
                ]
            )
            proposals.append(proposal)
        
        return proposals
    
    def _calculate_slotting_risk(self, context, aisle_id, time_window, conflicts):
        """Calculate risk score based on congestion, conflicts, and timing."""
        risk = 0.0
        
        # Congestion risk
        congestion = context.congestion_by_zone.get(aisle_id, 0.0)
        risk += congestion * 0.3  # Congestion contributes up to 0.3 to risk
        
        # Conflict risk
        if conflicts:
            risk += 0.2  # Potential conflicts add risk
        
        # Peak hours risk
        if self._is_peak_picking_hours(context, time_window):
            risk += 0.1  # Peak hours add risk
        
        return min(risk, 1.0)
    
    def _calculate_slotting_uncertainty(self, context, sku, from_loc, to_loc):
        """Calculate uncertainty based on data completeness and historical patterns."""
        uncertainty = 0.0
        
        # Data completeness
        if not context.inventory_at_location.get(from_loc):
            uncertainty += 0.2  # Missing inventory data
        
        if not context.location_capacity.get(to_loc):
            uncertainty += 0.2  # Missing capacity data
        
        # Historical pattern confidence
        # In production: Check if similar slotting moves have historical data
        # If no historical data, increase uncertainty
        if not self._has_historical_slotting_data(context, sku, to_loc):
            uncertainty += 0.1
        
        return min(uncertainty, 1.0)


# ============================================================================
# Replenishment Agent
# ============================================================================

class ReplenishmentAgent:
    """
    Personality: Prevents stockout at forward pick locations. Prefers proactive
    replenishment, batch operations, off-peak timing. High risk tolerance for
    stockout prevention, low tolerance for safety violations.
    
    Key traits:
    - Proactive: Replenishes when approaching reorder point, not after stockout
    - Requires 0.85+ confidence (lower than slotting due to urgency)
    - Escalates when stockout risk high but conflicts with high-priority picking
    - Always checks forklift availability, aisle access, stockout risk
    """
    
    def propose_actions(self, context: WarehouseContext) -> List[ProposedAction]:
        """
        Generate replenishment proposals to prevent stockouts.
        
        Logic:
        1. Identify locations approaching or below reorder point
        2. Calculate stockout risk (time until stockout, order dependencies)
        3. Evaluate constraints (forklift availability, aisle access, safety)
        4. Propose replenishment with timing that minimizes disruption
        5. Escalate if stockout risk high but conflicts with high-priority operations
        """
        proposals = []
        
        # Step 1: Identify locations needing replenishment
        # In production: Query semantic graph for locations below reorder point
        locations_needing_replenishment = self._identify_replenishment_needs(context)
        
        for location_data in locations_needing_replenishment:
            location_id = location_data['location_id']
            sku = location_data['sku']
            current_stock = location_data['current_stock']
            reorder_point = location_data['reorder_point']
            daily_consumption = location_data['daily_consumption']
            stockout_risk_hours = (current_stock - reorder_point) / daily_consumption * 24
            
            # Step 2: Check non-negotiable constraints
            constraints_checked = []
            can_proceed = True
            
            # Constraint: Never replenish if at or above reorder point
            if current_stock >= reorder_point:
                continue
            constraints_checked.append("reorder_point_threshold")
            
            # Constraint: Forklift availability
            available_forklift = self._find_available_forklift(context)
            if not available_forklift:
                # No forklift available - escalate
                self._escalate_to_orchestrator(
                    f"Replenishment needed at {location_id} but no forklift available"
                )
                continue
            constraints_checked.append("forklift_availability")
            
            # Constraint: Aisle access and safety
            aisle_id = self._get_aisle_from_location(location_id)
            if context.aisle_occupancy.get(aisle_id) == "locked":
                # Aisle locked - cannot proceed
                continue
            if self._has_forklift_worker_proximity_risk(context, aisle_id):
                # Safety violation risk - never proceed
                self._escalate_to_orchestrator(
                    f"Replenishment at {location_id} risks forklift-worker proximity violation"
                )
                continue
            constraints_checked.append("aisle_safety")
            constraints_checked.append("forklift_worker_proximity")
            
            # Constraint: Location capacity
            location_capacity = context.location_capacity.get(location_id, 0)
            proposed_quantity = min(
                location_capacity - current_stock,  # Don't overfill
                location_data['reserve_quantity_available']  # Don't exceed reserve
            )
            if proposed_quantity <= 0:
                continue
            constraints_checked.append("location_capacity")
            
            # Step 3: Calculate optimal timing
            # Prefer off-peak, but will interrupt if stockout risk is high
            if stockout_risk_hours > 4:
                # Low stockout risk - prefer off-peak
                proposed_time = self._find_off_peak_window(context, aisle_id)
            else:
                # High stockout risk - propose immediate (within constraints)
                proposed_time = self._find_earliest_safe_window(context, aisle_id)
            constraints_checked.append("timing_optimization")
            
            # Step 4: Check for conflicts
            potential_conflicts = []
            if self._has_active_picking_in_aisle(context, aisle_id, proposed_time):
                potential_conflicts.append(f"active_picking_in_aisle_{aisle_id}")
                # If stockout risk is high, still propose but escalate
                if stockout_risk_hours < 2:
                    # High stockout risk - propose but escalate conflict
                    self._escalate_to_orchestrator(
                        f"Replenishment at {location_id} conflicts with picking, "
                        f"but stockout risk is high ({stockout_risk_hours:.1f} hours)"
                    )
            
            # Step 5: Calculate risk and uncertainty
            risk_score = self._calculate_replenishment_risk(
                context, location_id, stockout_risk_hours, potential_conflicts
            )
            uncertainty = self._calculate_replenishment_uncertainty(
                context, location_id, sku, current_stock
            )
            confidence = 1.0 - uncertainty
            
            # Step 6: Only propose if confidence >= 0.85 (personality requirement)
            if confidence < 0.85:
                # Escalate uncertainty
                self._escalate_uncertainty(
                    f"Replenishment uncertainty for {location_id}: confidence {confidence:.2f}"
                )
                continue
            
            # Step 7: Generate proposal
            proposal = ProposedAction(
                agent_name="ReplenishmentAgent",
                action_type="replenishment",
                target_entities={
                    "location": location_id,
                    "sku": sku,
                    "from_location": location_data['reserve_location'],
                    "to_location": location_id,
                    "quantity": proposed_quantity,
                    "aisle": aisle_id
                },
                time_window={
                    "earliest_start": proposed_time['start'],
                    "latest_end": proposed_time['end']
                },
                required_resources=[available_forklift],
                priority=self._calculate_replenishment_priority(stockout_risk_hours, context),
                risk_score=risk_score,
                uncertainty=uncertainty,
                constraints_respected=constraints_checked,
                potential_conflicts=potential_conflicts,
                explanation=(
                    f"Replenish {sku} at {location_id}: {current_stock} units remaining "
                    f"(reorder point: {reorder_point}), projected stockout in {stockout_risk_hours:.1f} hours. "
                    f"Replenish {proposed_quantity} units from {location_data['reserve_location']}, "
                    f"estimated time: 15 minutes. "
                    f"Forklift {available_forklift} available, Aisle {aisle_id} available "
                    f"{proposed_time['start'].strftime('%H:%M')}-{proposed_time['end'].strftime('%H:%M')} "
                    f"(after picking completes), location capacity sufficient."
                ),
                confidence=confidence,
                alternatives=self._generate_replenishment_alternatives(context, location_data),
                data_sources=[
                    "semantic_graph:location_stock_levels",
                    "semantic_graph:reorder_points",
                    "historical:consumption_patterns",
                    "sensor:location_occupancy"
                ]
            )
            proposals.append(proposal)
        
        return proposals
    
    def _calculate_replenishment_risk(self, context, location_id, stockout_hours, conflicts):
        """Calculate risk: high stockout risk increases priority, conflicts add risk."""
        risk = 0.0
        
        # Stockout risk (inverted - high stockout risk = low proposal risk, high urgency)
        if stockout_hours < 2:
            risk += 0.1  # High urgency, but low risk of being wrong
        elif stockout_hours < 4:
            risk += 0.2
        else:
            risk += 0.3  # Lower urgency, more time to optimize
        
        # Conflict risk
        if conflicts:
            risk += 0.3  # Conflicts with other operations add risk
        
        # Safety risk (forklift-worker proximity)
        aisle_id = self._get_aisle_from_location(location_id)
        if context.worker_density.get(aisle_id, 0.0) > 2.5:
            risk += 0.2  # High worker density increases safety risk
        
        return min(risk, 1.0)
    
    def _calculate_replenishment_uncertainty(self, context, location_id, sku, current_stock):
        """Calculate uncertainty based on data completeness and stockout prediction confidence."""
        uncertainty = 0.0
        
        # Stock level data completeness
        if current_stock is None:
            uncertainty += 0.3  # Missing stock data
        
        # Consumption prediction confidence
        # In production: Check historical consumption pattern stability
        if not self._has_stable_consumption_pattern(context, location_id, sku):
            uncertainty += 0.2  # Unstable consumption pattern
        
        # Location availability confidence
        if context.location_status.get(location_id) != "available":
            uncertainty += 0.2  # Location status uncertain
        
        return min(uncertainty, 1.0)


# ============================================================================
# Picking Agent
# ============================================================================

class PickingAgent:
    """
    Personality: Ensures orders are picked accurately and on-time. Extremely low
    risk tolerance for SLA violations. Prefers SLA adherence over efficiency.
    Requires 0.95+ confidence for location availability.
    
    Key traits:
    - SLA-first: Will accept longer paths or higher cost to meet promise dates
    - Escalates immediately if promise date or cut-off time at risk
    - Always checks worker skills, location availability, order priorities
    - Never proposes picks from locations that semantic graph shows as empty
    """
    
    def propose_actions(self, context: WarehouseContext) -> List[ProposedAction]:
        """
        Generate picking proposals to fulfill customer orders.
        
        Logic:
        1. Identify orders needing picks (by promise date, cut-off time, priority)
        2. For each order, find optimal pick path and worker assignment
        3. Evaluate constraints (worker skills, location availability, SLA)
        4. Propose picks with clear SLA status and risk assessment
        5. Escalate immediately if SLA at risk or constraints cannot be satisfied
        """
        proposals = []
        
        # Step 1: Identify orders needing picks
        # In production: Query semantic graph for orders by promise date, priority
        orders_needing_picks = self._identify_orders_needing_picks(context)
        
        # Sort by priority: Tier 1 > Tier 2 > Tier 3, then by promise date
        orders_needing_picks.sort(
            key=lambda o: (self._get_priority_tier(o), o['promise_date'])
        )
        
        for order_data in orders_needing_picks:
            order_id = order_data['order_id']
            promise_date = order_data['promise_date']
            priority_tier = order_data['priority_tier']
            items = order_data['items']  # List of (sku, location, quantity)
            
            # Step 2: Calculate SLA status
            time_remaining = (promise_date - context.current_time).total_seconds() / 60
            sla_risk = self._calculate_sla_risk(time_remaining, priority_tier)
            
            # Step 3: Check non-negotiable constraints
            constraints_checked = []
            can_proceed = True
            
            # Constraint: Never propose if promise date already passed
            if time_remaining < 0:
                # SLA violation - escalate immediately
                self._escalate_to_orchestrator(
                    f"Order {order_id} promise date passed: {promise_date}"
                )
                continue
            
            # Constraint: Never propose picks from empty locations
            for sku, location_id, quantity in items:
                location_stock = context.inventory_at_location.get(location_id, 0)
                if location_stock < quantity:
                    # Location doesn't have enough stock - escalate
                    self._escalate_to_orchestrator(
                        f"Order {order_id} requires {quantity} of {sku} from {location_id}, "
                        f"but only {location_stock} available"
                    )
                    can_proceed = False
                    break
            if not can_proceed:
                continue
            constraints_checked.append("location_availability")
            
            # Constraint: Worker skills and availability
            required_skills = self._get_required_skills_for_order(order_data, context)
            available_worker = self._find_available_worker_with_skills(
                context, required_skills, time_remaining
            )
            if not available_worker:
                # No worker available - escalate
                self._escalate_to_orchestrator(
                    f"Order {order_id} requires worker with skills {required_skills}, "
                    f"but none available within SLA window"
                )
                continue
            constraints_checked.append("worker_skills")
            constraints_checked.append("worker_availability")
            
            # Constraint: Aisle access and safety
            aisles_needed = set(self._get_aisle_from_location(loc) for _, loc, _ in items)
            for aisle_id in aisles_needed:
                if context.aisle_occupancy.get(aisle_id) == "locked":
                    # Aisle locked - cannot proceed
                    self._escalate_to_orchestrator(
                        f"Order {order_id} requires Aisle {aisle_id} which is locked"
                    )
                    can_proceed = False
                    break
            if not can_proceed:
                continue
            constraints_checked.append("aisle_access")
            constraints_checked.append("safety_locks")
            
            # Step 4: Calculate optimal pick path
            pick_path = self._calculate_optimal_pick_path(items, available_worker, context)
            estimated_pick_time = self._estimate_pick_time(pick_path, context)
            
            # Step 5: Check if pick can complete within SLA
            if time_remaining < estimated_pick_time + 15:  # 15 min buffer for pack/ship
                # SLA at risk - escalate immediately
                self._escalate_to_orchestrator(
                    f"Order {order_id} SLA at risk: {time_remaining:.0f} min remaining, "
                    f"estimated pick time: {estimated_pick_time:.0f} min"
                )
                continue
            
            # Step 6: Check for conflicts
            potential_conflicts = []
            for aisle_id in aisles_needed:
                if self._has_conflicting_operations(context, aisle_id, pick_path['time_window']):
                    potential_conflicts.append(f"conflicting_operations_in_aisle_{aisle_id}")
            
            # Step 7: Calculate risk and uncertainty
            risk_score = self._calculate_picking_risk(
                context, order_data, time_remaining, potential_conflicts
            )
            uncertainty = self._calculate_picking_uncertainty(
                context, items, available_worker, pick_path
            )
            confidence = 1.0 - uncertainty
            
            # Step 8: Only propose if confidence >= 0.95 (personality requirement)
            if confidence < 0.95:
                # Escalate uncertainty - never guess on location availability
                self._escalate_uncertainty(
                    f"Picking uncertainty for Order {order_id}: confidence {confidence:.2f}"
                )
                continue
            
            # Step 9: Generate proposal
            proposal = ProposedAction(
                agent_name="PickingAgent",
                action_type="pick_assignment",
                target_entities={
                    "order_id": order_id,
                    "worker_id": available_worker,
                    "items": items,
                    "pick_path": pick_path,
                    "aisles": list(aisles_needed)
                },
                time_window={
                    "earliest_start": pick_path['start_time'],
                    "latest_end": pick_path['end_time']
                },
                required_resources=[available_worker, "cart", "scanner"],
                priority=self._calculate_picking_priority(priority_tier, time_remaining),
                risk_score=risk_score,
                uncertainty=uncertainty,
                constraints_respected=constraints_checked,
                potential_conflicts=potential_conflicts,
                explanation=(
                    f"Order {order_id}: {priority_tier} customer, promise date: {promise_date.strftime('%H:%M')}, "
                    f"{time_remaining:.0f} minutes remaining, {len(items)} items. "
                    f"Assign Worker {available_worker} to pick from Locations {[loc for _, loc, _ in items]}, "
                    f"estimated time: {estimated_pick_time:.0f} minutes. "
                    f"On track: Pick completes {pick_path['end_time'].strftime('%H:%M')}, "
                    f"pack/ship by {(pick_path['end_time'] + timedelta(minutes=15)).strftime('%H:%M')}, "
                    f"{time_remaining - estimated_pick_time - 15:.0f}-minute buffer before promise."
                ),
                confidence=confidence,
                alternatives=self._generate_picking_alternatives(context, order_data, items),
                data_sources=[
                    "semantic_graph:order_details",
                    "semantic_graph:location_inventory",
                    "semantic_graph:worker_skills",
                    "historical:pick_time_estimates"
                ]
            )
            proposals.append(proposal)
        
        return proposals
    
    def _calculate_picking_risk(self, context, order_data, time_remaining, conflicts):
        """Calculate risk: SLA risk dominates, conflicts add operational risk."""
        risk = 0.0
        
        # SLA risk (inverted - tight SLA = low proposal risk, high urgency)
        if time_remaining < 60:
            risk += 0.1  # Very tight, but proposal is correct
        elif time_remaining < 120:
            risk += 0.2
        else:
            risk += 0.3  # More time = more optimization opportunity = slightly higher risk
        
        # Conflict risk
        if conflicts:
            risk += 0.2  # Conflicts add operational risk
        
        # Priority risk (lower priority = slightly higher risk of being deprioritized)
        if order_data['priority_tier'] == "Tier 3":
            risk += 0.1
        
        return min(risk, 1.0)
    
    def _calculate_picking_uncertainty(self, context, items, worker, pick_path):
        """Calculate uncertainty: requires 0.95+ confidence for location availability."""
        uncertainty = 0.0
        
        # Location availability confidence (critical - never guess)
        for sku, location_id, quantity in items:
            if location_id not in context.inventory_at_location:
                uncertainty += 0.3  # Missing location data - high uncertainty
            elif context.inventory_at_location[location_id] < quantity:
                uncertainty += 0.5  # Insufficient stock - very high uncertainty
        
        # Worker availability confidence
        if worker not in context.worker_availability or not context.worker_availability[worker]:
            uncertainty += 0.2
        
        # Pick time estimation confidence
        if not self._has_historical_pick_time_data(context, pick_path):
            uncertainty += 0.1  # No historical data for time estimation
        
        return min(uncertainty, 1.0)


# ============================================================================
# Dock/Yard Agent
# ============================================================================

class DockYardAgent:
    """
    Personality: Optimizes dock door utilization and trailer dwell times.
    Prefers appointment adherence, outbound priority during peak shipping.
    High risk tolerance for urgent shipments.
    
    Key traits:
    - Appointment-first: Prioritizes meeting scheduled appointment times
    - Outbound priority: Ensures outbound operations have dock access during cut-offs
    - Escalates when appointments conflict with carrier cut-offs or urgent shipments
    - Always checks door availability, equipment status, trailer status
    """
    
    def propose_actions(self, context: WarehouseContext) -> List[ProposedAction]:
        """
        Generate dock/yard proposals for inbound receiving and outbound shipping.
        
        Logic:
        1. Identify inbound trailers needing receiving and outbound trailers needing shipping
        2. Match trailers to dock doors based on appointment times, priorities, equipment
        3. Evaluate constraints (door availability, equipment, carrier cut-offs)
        4. Propose dock assignments with timing that meets appointments and cut-offs
        5. Escalate if appointments conflict with cut-offs or urgent shipments blocked
        """
        proposals = []
        
        # Step 1: Identify trailers needing dock assignment
        inbound_trailers = self._identify_inbound_trailers(context)
        outbound_trailers = self._identify_outbound_trailers(context)
        
        # Step 2: Process outbound trailers first (priority during peak shipping)
        for trailer_data in outbound_trailers:
            trailer_id = trailer_data['trailer_id']
            appointment_time = trailer_data['appointment_time']
            carrier_cutoff = trailer_data['carrier_cutoff']
            priority = trailer_data.get('priority', 'standard')
            
            # Step 3: Check non-negotiable constraints
            constraints_checked = []
            
            # Constraint: Carrier cut-off time
            time_to_cutoff = (carrier_cutoff - context.current_time).total_seconds() / 60
            if time_to_cutoff < 0:
                # Cut-off passed - escalate
                self._escalate_to_orchestrator(
                    f"Trailer {trailer_id} carrier cut-off passed: {carrier_cutoff}"
                )
                continue
            constraints_checked.append("carrier_cutoff")
            
            # Constraint: Dock door availability
            available_door = self._find_available_dock_door(
                context, appointment_time, "outbound"
            )
            if not available_door:
                # No door available - escalate
                self._escalate_to_orchestrator(
                    f"Trailer {trailer_id} needs dock door at {appointment_time}, but none available"
                )
                continue
            constraints_checked.append("dock_door_availability")
            
            # Constraint: Equipment availability (dock leveler, yard truck)
            required_equipment = self._get_required_equipment_for_trailer(trailer_data, context)
            if not all(context.equipment_status.get(eq) == "operational" for eq in required_equipment):
                # Equipment unavailable - escalate
                self._escalate_to_orchestrator(
                    f"Trailer {trailer_id} requires equipment {required_equipment}, but not all operational"
                )
                continue
            constraints_checked.append("equipment_availability")
            
            # Step 4: Calculate timing
            proposed_start = max(appointment_time, context.current_time)
            estimated_duration = self._estimate_trailer_processing_time(trailer_data, context)
            proposed_end = proposed_start + timedelta(minutes=estimated_duration)
            
            # Step 5: Check if can meet cut-off
            if proposed_end > carrier_cutoff:
                # Cannot meet cut-off - escalate
                self._escalate_to_orchestrator(
                    f"Trailer {trailer_id} cannot meet carrier cut-off {carrier_cutoff} "
                    f"with proposed completion {proposed_end}"
                )
                continue
            
            # Step 6: Check for conflicts
            potential_conflicts = []
            if self._has_conflicting_dock_operations(context, available_door, proposed_start, proposed_end):
                potential_conflicts.append(f"conflicting_operations_at_door_{available_door}")
            
            # Step 7: Calculate risk and uncertainty
            risk_score = self._calculate_dock_risk(
                context, trailer_data, time_to_cutoff, potential_conflicts
            )
            uncertainty = self._calculate_dock_uncertainty(
                context, trailer_data, available_door
            )
            confidence = 1.0 - uncertainty
            
            # Step 8: Generate proposal
            proposal = ProposedAction(
                agent_name="DockYardAgent",
                action_type="dock_assignment",
                target_entities={
                    "trailer_id": trailer_id,
                    "dock_door": available_door,
                    "direction": "outbound",
                    "appointment_time": appointment_time,
                    "carrier_cutoff": carrier_cutoff
                },
                time_window={
                    "earliest_start": proposed_start,
                    "latest_end": proposed_end
                },
                required_resources=[available_door] + required_equipment,
                priority=self._calculate_dock_priority(priority, time_to_cutoff),
                risk_score=risk_score,
                uncertainty=uncertainty,
                constraints_respected=constraints_checked,
                potential_conflicts=potential_conflicts,
                explanation=(
                    f"Schedule outbound Trailer {trailer_id} at Dock Door {available_door}, "
                    f"start: {proposed_start.strftime('%H:%M')}, carrier cut-off: {carrier_cutoff.strftime('%H:%M')}. "
                    f"Dock Door {available_door} available, Trailer {trailer_id} on-site, "
                    f"yard truck available, appointment confirmed."
                ),
                confidence=confidence,
                alternatives=self._generate_dock_alternatives(context, trailer_data),
                data_sources=[
                    "semantic_graph:trailer_appointments",
                    "semantic_graph:dock_door_status",
                    "semantic_graph:equipment_status"
                ]
            )
            proposals.append(proposal)
        
        # Step 9: Process inbound trailers (similar logic, but different priorities)
        # ... (similar structure, but inbound-specific constraints and priorities)
        
        return proposals
    
    def _calculate_dock_risk(self, context, trailer_data, time_to_cutoff, conflicts):
        """Calculate risk: cut-off proximity and conflicts add risk."""
        risk = 0.0
        
        # Cut-off risk (inverted - tight cut-off = low proposal risk, high urgency)
        if time_to_cutoff < 30:
            risk += 0.1  # Very tight, but proposal is correct
        elif time_to_cutoff < 60:
            risk += 0.2
        else:
            risk += 0.3
        
        # Conflict risk
        if conflicts:
            risk += 0.3  # Dock conflicts are significant
        
        # Urgent shipment risk
        if trailer_data.get('priority') == 'urgent':
            risk += 0.1  # Urgent shipments have higher operational risk
        
        return min(risk, 1.0)


# ============================================================================
# Labor Sync Agent
# ============================================================================

class LaborSyncAgent:
    """
    Personality: Optimizes worker assignment across zones and tasks. Prefers
    skill-based assignment, fair distribution, zone consistency. Low risk
    tolerance for safety violations, moderate tolerance for efficiency.
    
    Key traits:
    - Skill-first: Matches worker skills to task requirements
    - Fair distribution: Balances workload to prevent overload/idle
    - Escalates when high-priority tasks require unavailable skills
    - Always checks worker skills, capacity, shift rules, fatigue
    """
    
    def propose_actions(self, context: WarehouseContext) -> List[ProposedAction]:
        """
        Generate labor assignment proposals to optimize worker utilization.
        
        Logic:
        1. Identify tasks needing worker assignment (from other agents or system)
        2. Match tasks to workers based on skills, capacity, proximity, fairness
        3. Evaluate constraints (skills, capacity, shift rules, fatigue)
        4. Propose assignments that balance efficiency and fairness
        5. Escalates when high-priority tasks cannot be assigned
        """
        proposals = []
        
        # Step 1: Identify tasks needing assignment
        # In production: Receive task requests from other agents or system
        tasks_needing_assignment = self._identify_tasks_needing_assignment(context)
        
        for task_data in tasks_needing_assignment:
            task_id = task_data['task_id']
            task_type = task_data['task_type']
            required_skills = task_data['required_skills']
            task_location = task_data['location']
            task_priority = task_data.get('priority', 5)
            
            # Step 2: Check non-negotiable constraints
            constraints_checked = []
            
            # Constraint: Worker skills
            available_workers = [
                w for w in context.worker_availability.keys()
                if context.worker_availability[w] and
                all(skill in context.worker_skills.get(w, []) for skill in required_skills)
            ]
            if not available_workers:
                # No worker with required skills - escalate
                self._escalate_to_orchestrator(
                    f"Task {task_id} requires skills {required_skills}, but no worker available"
                )
                continue
            constraints_checked.append("worker_skills")
            
            # Constraint: Worker capacity
            workers_with_capacity = [
                w for w in available_workers
                if context.worker_capacity.get(w, 0) >= task_data['estimated_duration']
            ]
            if not workers_with_capacity:
                # No worker with capacity - escalate
                self._escalate_to_orchestrator(
                    f"Task {task_id} requires {task_data['estimated_duration']} minutes, "
                    f"but no worker has capacity"
                )
                continue
            constraints_checked.append("worker_capacity")
            
            # Constraint: Shift rules and fatigue
            eligible_workers = []
            for worker_id in workers_with_capacity:
                if self._check_shift_rules(context, worker_id, task_data):
                    if self._check_fatigue_level(context, worker_id):
                        eligible_workers.append(worker_id)
            
            if not eligible_workers:
                # No eligible worker - escalate
                self._escalate_to_orchestrator(
                    f"Task {task_id} cannot be assigned: shift rules or fatigue constraints"
                )
                continue
            constraints_checked.append("shift_rules")
            constraints_checked.append("fatigue_constraints")
            
            # Step 3: Select best worker (skill match, capacity, proximity, fairness)
            assigned_worker = self._select_best_worker(
                context, eligible_workers, task_location, task_priority
            )
            
            # Step 4: Calculate risk and uncertainty
            risk_score = self._calculate_labor_risk(
                context, task_data, assigned_worker
            )
            uncertainty = self._calculate_labor_uncertainty(
                context, task_data, assigned_worker
            )
            confidence = 1.0 - uncertainty
            
            # Step 5: Generate proposal
            proposal = ProposedAction(
                agent_name="LaborSyncAgent",
                action_type="labor_assignment",
                target_entities={
                    "task_id": task_id,
                    "worker_id": assigned_worker,
                    "task_type": task_type,
                    "location": task_location
                },
                time_window={
                    "earliest_start": context.current_time,
                    "latest_end": context.current_time + timedelta(minutes=task_data['estimated_duration'])
                },
                required_resources=[assigned_worker],
                priority=task_priority,
                risk_score=risk_score,
                uncertainty=uncertainty,
                constraints_respected=constraints_checked,
                potential_conflicts=[],  # Labor agent coordinates, conflicts handled by orchestrator
                explanation=(
                    f"Assign Worker {assigned_worker} to Task {task_id} ({task_type}) at {task_location}. "
                    f"Worker {assigned_worker} has required skills {required_skills}, "
                    f"capacity: {context.worker_capacity.get(assigned_worker, 0)} minutes, "
                    f"current zone: {context.worker_location.get(assigned_worker, 'unknown')}. "
                    f"Assignment optimizes labor utilization and maintains fair workload distribution."
                ),
                confidence=confidence,
                alternatives=self._generate_labor_alternatives(context, task_data, eligible_workers),
                data_sources=[
                    "semantic_graph:worker_skills",
                    "semantic_graph:worker_capacity",
                    "semantic_graph:task_requirements",
                    "historical:worker_performance"
                ]
            )
            proposals.append(proposal)
        
        return proposals
    
    def _calculate_labor_risk(self, context, task_data, worker):
        """Calculate risk: safety violations and unfair distribution add risk."""
        risk = 0.0
        
        # Skill mismatch risk
        required_skills = task_data['required_skills']
        worker_skills = context.worker_skills.get(worker, [])
        if not all(skill in worker_skills for skill in required_skills):
            risk += 0.5  # High risk if skills don't match
        
        # Capacity risk
        if context.worker_capacity.get(worker, 0) < task_data['estimated_duration']:
            risk += 0.3  # High risk if insufficient capacity
        
        # Fairness risk (workload imbalance)
        worker_load = self._calculate_worker_load(context, worker)
        avg_load = self._calculate_average_worker_load(context)
        if worker_load > avg_load * 1.2:  # 20% above average
            risk += 0.1  # Slight risk if unfair distribution
        
        return min(risk, 1.0)


# ============================================================================
# Inventory Accuracy Agent
# ============================================================================

class InventoryAccuracyAgent:
    """
    Personality: Maintains alignment between system and physical inventory.
    Prefers investigation over immediate correction, targeted cycle counts,
    evidence-based recommendations. Extremely low risk tolerance for customer
    impact. Requires 0.95+ confidence before recommending adjustment.
    
    Key traits:
    - Investigation-first: Investigates root cause before recommending correction
    - Advisory only: Never executes adjustments, only recommends
    - Escalates immediately if discrepancy risks customer order
    - Always checks evidence (cycle counts, sensor data, transaction history)
    """
    
    def propose_actions(self, context: WarehouseContext) -> List[ProposedAction]:
        """
        Generate inventory accuracy proposals (investigations and recommendations).
        
        Logic:
        1. Detect inventory discrepancies (system vs physical, sensor anomalies)
        2. Investigate root causes (transaction history, location misidentification)
        3. Evaluate customer impact (orders requiring location)
        4. Recommend cycle count verification or adjustment
        5. Escalate immediately if customer order at risk
        """
        proposals = []
        
        # Step 1: Detect discrepancies
        # In production: Compare semantic graph inventory with sensor data, cycle counts
        discrepancies = self._detect_inventory_discrepancies(context)
        
        for discrepancy in discrepancies:
            location_id = discrepancy['location_id']
            sku = discrepancy['sku']
            system_quantity = discrepancy['system_quantity']
            physical_quantity = discrepancy['physical_quantity']
            discrepancy_amount = system_quantity - physical_quantity
            
            # Step 2: Investigate root cause
            investigation = self._investigate_discrepancy_root_cause(
                context, location_id, sku, discrepancy_amount
            )
            
            # Step 3: Check customer impact
            orders_requiring_location = self._find_orders_requiring_location(
                context, location_id, sku
            )
            customer_impact_risk = len(orders_requiring_location) > 0
            
            # Step 4: Check non-negotiable constraints
            constraints_checked = []
            
            # Constraint: Never recommend adjustment without evidence
            if not investigation['has_evidence']:
                # No evidence - cannot recommend
                continue
            constraints_checked.append("evidence_required")
            
            # Constraint: Escalate immediately if customer order at risk
            if customer_impact_risk:
                # Customer order at risk - escalate immediately
                self._escalate_to_orchestrator(
                    f"Inventory discrepancy at {location_id}: {discrepancy_amount} units, "
                    f"risks customer orders {[o['order_id'] for o in orders_requiring_location]}"
                )
                # Still propose investigation, but flag as urgent
                proposal_priority = 10  # Critical
            else:
                proposal_priority = 5  # Standard
            
            # Step 5: Calculate risk and uncertainty
            risk_score = self._calculate_inventory_risk(
                context, discrepancy, customer_impact_risk
            )
            uncertainty = self._calculate_inventory_uncertainty(
                context, discrepancy, investigation
            )
            confidence = 1.0 - uncertainty
            
            # Step 6: Only propose if confidence >= 0.95 (personality requirement)
            if confidence < 0.95:
                # Escalate uncertainty - never guess on inventory adjustments
                self._escalate_uncertainty(
                    f"Inventory discrepancy uncertainty at {location_id}: confidence {confidence:.2f}"
                )
                continue
            
            # Step 7: Generate proposal (advisory only - cycle count recommendation)
            proposal = ProposedAction(
                agent_name="InventoryAccuracyAgent",
                action_type="cycle_count_recommendation",  # Advisory, not execution
                target_entities={
                    "location_id": location_id,
                    "sku": sku,
                    "system_quantity": system_quantity,
                    "physical_quantity": physical_quantity,
                    "discrepancy_amount": discrepancy_amount,
                    "investigation": investigation
                },
                time_window={
                    "earliest_start": self._find_optimal_cycle_count_time(context, location_id),
                    "latest_end": self._find_optimal_cycle_count_time(context, location_id) + timedelta(minutes=15)
                },
                required_resources=["cycle_counter"],  # Human or automated
                priority=proposal_priority,
                risk_score=risk_score,
                uncertainty=uncertainty,
                constraints_respected=constraints_checked,
                potential_conflicts=[],  # Cycle counts scheduled during low activity
                explanation=(
                    f"Location {location_id}: System shows {system_quantity} units of {sku}, "
                    f"physical count suggests {physical_quantity} units, discrepancy: {discrepancy_amount} units. "
                    f"Investigation: {investigation['root_cause_hypothesis']}. "
                    f"Recommend: Cycle count verification, then adjust system to {physical_quantity} if verified, "
                    f"investigate missing {abs(discrepancy_amount)} units. "
                    f"{'URGENT: Customer orders at risk' if customer_impact_risk else 'Standard investigation'}."
                ),
                confidence=confidence,
                alternatives=[],  # No alternatives for cycle count - must verify
                data_sources=[
                    "semantic_graph:location_inventory",
                    "sensor:location_occupancy",
                    "transaction_history:location_movements",
                    "cycle_count_history:location_patterns"
                ]
            )
            proposals.append(proposal)
        
        return proposals
    
    def _calculate_inventory_risk(self, context, discrepancy, customer_impact):
        """Calculate risk: customer impact dominates, large discrepancies add risk."""
        risk = 0.0
        
        # Customer impact risk (critical)
        if customer_impact:
            risk += 0.1  # High urgency, but investigation is correct action
        
        # Discrepancy magnitude risk
        discrepancy_amount = abs(discrepancy['discrepancy_amount'])
        if discrepancy_amount > 10:
            risk += 0.2  # Large discrepancies suggest systemic issue
        elif discrepancy_amount > 5:
            risk += 0.1
        
        # Location criticality risk
        location_id = discrepancy['location_id']
        if location_id.startswith("A-"):  # Forward pick zone
            risk += 0.1  # Forward pick discrepancies more critical
        
        return min(risk, 1.0)
    
    def _calculate_inventory_uncertainty(self, context, discrepancy, investigation):
        """Calculate uncertainty: requires 0.95+ confidence before recommending adjustment."""
        uncertainty = 0.0
        
        # Evidence completeness
        if not investigation['has_evidence']:
            uncertainty += 0.5  # No evidence - very high uncertainty
        
        # Investigation confidence
        if investigation['confidence'] < 0.8:
            uncertainty += 0.3  # Low investigation confidence
        
        # Physical count confidence
        if discrepancy.get('physical_count_method') == 'estimated':
            uncertainty += 0.2  # Estimated counts less reliable
        
        # Transaction history completeness
        if not investigation.get('has_complete_transaction_history'):
            uncertainty += 0.2  # Missing transaction data
        
        return min(uncertainty, 1.0)


# ============================================================================
# Helper Methods (Placeholder Implementations)
# ============================================================================

# These methods would be implemented in production to query semantic graph,
# evaluate constraints, calculate metrics, etc. Shown here as placeholders
# to illustrate the behavior specification.

def _escalate_to_orchestrator(self, message: str):
    """Send escalation message to orchestrator."""
    # In production: Send event to orchestrator via event bus
    pass

def _escalate_uncertainty(self, message: str):
    """Escalate when uncertainty is too high to proceed."""
    # In production: Send uncertainty escalation to orchestrator
    pass

# Additional helper methods would be implemented similarly:
# - _identify_slotting_opportunities()
# - _check_location_compatibility()
# - _calculate_optimal_time_window()
# - _find_available_forklift()
# - _identify_orders_needing_picks()
# - _calculate_optimal_pick_path()
# - etc.

