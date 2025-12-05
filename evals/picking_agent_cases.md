# PickingAgent Evaluation Cases: Detailed Test Scenarios for Agent-Level Evaluation

**Document Version:** 1.0  
**Author:** Senior Product Management  
**Date:** December 2025  
**Audience:** Engineering Teams, Quality Assurance, Product Strategy

---

## 1. Purpose

The PickingAgent is an ideal candidate for deep evaluation because it operates at the critical intersection of customer-facing SLAs, physical safety constraints, and operational efficiency. Unlike tools that perform deterministic computations, the PickingAgent makes goal-directed decisions about when to prioritize orders, how to sequence picks, and when to escalate capacity constraints. These decisions directly impact customer satisfaction (order promise dates), warehouse safety (aisle congestion, worker assignments), and operational costs (labor utilization, travel distance). By defining explicit evaluation cases for PickingAgent, we establish a concrete behavioral contract that engineering teams can translate into automated tests, enabling safe deployment and continuous improvement.

This document applies the three-level evaluation framework defined in `evals/evaluation_framework.md` to PickingAgent specifically. It focuses on the **agent level** (Level 2) evaluation, which measures personality alignment, tool usage correctness, escalation behavior, and explanation quality. While this document assumes tools behave according to their contracts (Level 1) and may reference system-level behaviors (Level 3), its primary purpose is to define testable scenarios that verify PickingAgent behaves consistently with its defined personality in `agent_design/agent_personalities.md` and uses tools correctly as specified in `tool_contracts/tool_catalog.md`.

---

## 2. Scope and Assumptions

### What is in Scope

These evaluations focus on **PickingAgent behavior** in response to different combinations of:

- **Service level pressure:** Orders with varying promise dates, priority tiers, and cut-off times
- **Labor capacity:** Worker availability, skills, capacity, and fatigue constraints
- **Congestion:** Aisle occupancy, worker density, and resource competition
- **Data quality:** Location availability confidence, inventory accuracy, and sensor reliability

The evaluations verify that PickingAgent:
- Uses tools correctly (wave builder, pick path optimizer, SLA risk estimator, workload balancer, congestion estimator, labor capacity forecaster)
- Escalates appropriately when capacity is insufficient or uncertainty is high
- Generates explanations that are clear, evidence-based, and aligned with its personality
- Behaves consistently across similar scenarios

### What is Not in Scope

- **Exact tool implementations:** Tools are assumed to behave according to their contracts. Tool correctness is evaluated separately at Level 1.
- **User interface pixel detail:** UI design and visual presentation are out of scope. This document focuses on agent behavior and decision logic.
- **Hardware reliability:** Sensor failures, network outages, and equipment breakdowns are not evaluated here. These are system-level concerns.

### Assumptions

- **Tools behave according to their contracts:** Tool outputs are deterministic and correct. The evaluation harness may mock tool outputs to create controlled test scenarios.
- **Semantic warehouse graph provides accurate state:** Inventory locations, worker availability, and aisle occupancy are accurately represented in the graph.
- **Orchestrator handles conflict resolution:** When PickingAgent escalates conflicts, the Orchestrator (evaluated separately) resolves them according to global rules.

---

## 3. Evaluation Dimensions for PickingAgent

This document evaluates PickingAgent across five key dimensions that align with the agent-level evaluation objectives:

### 3.1 Personality Alignment

**What it means:** PickingAgent behaves consistently with its defined personality (see `agent_design/agent_personalities.md`). The agent prioritizes SLA adherence over efficiency, escalates immediately when promise dates are at risk, and requires 0.95+ confidence for location availability before proposing picks.

**Success criteria:**
- Agent never proposes picks from locations with confidence < 0.95
- Agent escalates immediately when promise date or cut-off time is at risk
- Agent accepts suboptimal pick paths if required to meet SLA commitments
- Agent explanations mention service level proximity and time buffers

### 3.2 Tool Usage Correctness

**What it means:** PickingAgent calls the right tools under the right preconditions, respects tool contracts, and interprets tool outputs correctly.

**Success criteria:**
- Agent calls SLA Risk Estimator before proposing pick assignments
- Agent uses wave/batch builder to group orders efficiently
- Agent uses pick path optimizer with valid location IDs and worker constraints
- Agent interprets congestion scores correctly (does not treat as binary flags)
- Agent handles tool errors gracefully (retries with backoff, escalates if retries fail)

### 3.3 Escalation Behaviour

**What it means:** PickingAgent escalates to Orchestrator or planner (HITL) when uncertainty exceeds thresholds, capacity is insufficient, or constraints cannot be satisfied.

**Success criteria:**
- Agent escalates when labor capacity is insufficient to meet all promise dates
- Agent escalates when location availability confidence < 0.95
- Agent escalates when promise date or cut-off time is at risk
- Agent escalates when required worker skills or equipment are unavailable
- Escalations include required information (current state, constraints, requested action)

### 3.4 Explanation Quality

**What it means:** PickingAgent generates explanations that are clear, structured, evidence-based, and useful to the Orchestrator and planner.

**Success criteria:**
- Explanations include order context (priority tier, promise date, time remaining)
- Explanations include SLA status (on track, at risk, buffer time)
- Explanations include constraints evaluated (worker skills, location availability, aisle access)
- Explanations include alternatives considered (if any)
- Explanations mention data sources (semantic graph queries, tool outputs)

### 3.5 Consistency Across Similar Scenarios

**What it means:** PickingAgent behaves consistently when faced with similar warehouse contexts, avoiding unpredictable variations that erode trust.

**Success criteria:**
- Agent makes similar decisions for similar order priorities and SLA pressures
- Agent applies escalation thresholds consistently (does not escalate randomly)
- Agent uses similar explanation structures across similar scenarios
- Agent prioritizes orders consistently (Tier 1 > Tier 2 > Tier 3, expedite > standard)

---

## 4. Scenario Design Framework

PickingAgent evaluation scenarios can be thought of as a grid with four key variables:

### 4.1 Service Level Pressure

- **Low:** Orders have generous due times (> 4 hours remaining), no expedite flags, standard priority tiers
- **Medium:** Orders have moderate due times (1-4 hours remaining), some expedite flags, mix of priority tiers
- **High:** Orders have tight due times (< 1 hour remaining), multiple expedite flags, high proportion of Tier 1 orders

### 4.2 Labor Sufficiency

- **Surplus:** More workers available than required, workers have excess capacity, all required skills present
- **Just enough:** Workers available match demand, capacity is sufficient but tight, all required skills present
- **Insufficient:** Fewer workers available than required, capacity clearly insufficient, some required skills missing

### 4.3 Congestion

- **Low:** Aisle occupancy is minimal, worker density is below thresholds, no resource competition
- **Moderate:** Some aisles have moderate occupancy, worker density approaching thresholds, some resource competition
- **High:** Multiple aisles heavily loaded, worker density at or above thresholds, significant resource competition

### 4.4 Data Quality or Confidence

- **Clean:** All location data is high confidence (0.95+), inventory levels are accurate, sensor data is reliable
- **Partial:** Some locations have lower confidence (0.80-0.94), some inventory discrepancies detected, sensor data is partially reliable
- **Conflicting:** Some locations have low confidence (< 0.80), inventory discrepancies detected, sensor data conflicts with system records

### 4.5 Scenario Selection

The detailed cases below select representative combinations from this grid to stress different aspects of PickingAgent behavior:

- **Case 1:** High service level pressure, sufficient labor, low congestion → Tests SLA prioritization and tool usage
- **Case 2:** High service level pressure, insufficient labor → Tests escalation behavior and capacity acknowledgment
- **Case 3:** Low service level pressure, high congestion → Tests congestion awareness and safety-first behavior
- **Case 4:** Conflicting or partial data → Tests uncertainty handling and data confidence differentiation

Additional cases can be added to cover edge cases, regression scenarios, or specific failure modes discovered in production.

---

## 5. Detailed Evaluation Cases

Each case follows a consistent template that enables engineering teams to implement automated tests:

- **Scenario name:** Descriptive identifier for the test case
- **Situation or context:** Warehouse state, orders, workers, and constraints
- **Relevant tools and signals:** Which tools PickingAgent should call and what outputs they should produce
- **Expected PickingAgent behaviour:** What the agent should do, propose, or escalate
- **Metrics and observations:** What to measure and observe in the agent's behavior
- **Pass or fail criteria:** Clear thresholds for success and failure

---

### 5.1 Case 1: High Service Level Pressure, Sufficient Labor, Low Congestion

**Scenario Name:** `picking_agent_high_sla_sufficient_labor_low_congestion`

**Situation or Context:**

- **Orders:** 15 orders pending, with varying promise dates:
  - 5 orders due in 60-90 minutes (Tier 1 customers, expedite flags)
  - 5 orders due in 3-4 hours (Tier 2 customers, standard priority)
  - 5 orders due in 6-8 hours (Tier 3 customers, standard priority)
- **Labor:** 8 workers available, all with required skills, average capacity: 4 hours remaining per worker
- **Congestion:** All aisles have low occupancy (< 0.3 congestion score), worker density: 1.5 workers per 100 sq ft (below 3.0 threshold)
- **Data Quality:** All location data is high confidence (0.95+), inventory levels accurate

**Relevant Tools and Signals:**

- **Service Level Risk Estimator:** Should return high risk scores (0.7-0.9) for orders due in 60-90 minutes, low risk scores (< 0.2) for orders due in 6-8 hours
- **Wave or Batch Builder:** Should group orders by priority and promise date, creating early waves for near-due orders
- **Pick Path Optimizer:** Should generate efficient paths for each wave, minimizing travel time
- **Picker Workload Balancer:** Should distribute work evenly across 8 workers, no worker overloaded
- **Congestion Estimator:** Should return low congestion scores (< 0.3) for all aisles
- **Labor Capacity Forecaster:** Should indicate sufficient capacity (8 workers × 4 hours = 32 hours available, 15 orders × 1.5 hours average = 22.5 hours required)

**Expected PickingAgent Behaviour:**

1. **Tool Usage:**
   - Calls Service Level Risk Estimator for all 15 orders
   - Calls Wave or Batch Builder with orders sorted by priority and promise date
   - Calls Pick Path Optimizer for each wave with worker assignments
   - Calls Picker Workload Balancer to distribute work across 8 workers
   - Calls Congestion Estimator to verify low congestion (may skip if confident)
   - Calls Labor Capacity Forecaster to verify sufficient capacity

2. **Prioritization:**
   - Proposes early waves (Wave 1, Wave 2) for 5 orders due in 60-90 minutes
   - Proposes later waves (Wave 3, Wave 4) for 5 orders due in 3-4 hours
   - Proposes final waves (Wave 5) for 5 orders due in 6-8 hours
   - Does not unnecessarily reshuffle low-risk work (orders due in 6-8 hours can wait)

3. **Proposed Actions:**
   - High priority (8-10) for near-due waves (60-90 minutes remaining)
   - Low priority (3-5) for later waves (6-8 hours remaining)
   - Low risk scores (< 0.2) for all proposals (sufficient capacity, low congestion)
   - Low uncertainty (< 0.1) for all proposals (high confidence in location availability)

4. **Explanations:**
   - Mentions service level proximity ("Order #7892: Tier 1 customer, promise date: 10:30 AM, 75 minutes remaining")
   - Mentions time buffers ("On track: Pick completes 9:30 AM, pack/ship by 9:45 AM, 45-minute buffer before promise")
   - Mentions low risk and low uncertainty ("All locations confirmed available, sufficient worker capacity, low congestion")

5. **Escalation:**
   - Does not escalate (sufficient capacity, low risk, high confidence)
   - Proceeds autonomously with proposals

**Metrics and Observations:**

- **Percentage of service level critical orders placed in early waves:** Should be 100% (all 5 orders due in 60-90 minutes in Wave 1 or Wave 2)
- **Presence of clear service level based rationale in explanations:** Should be 100% (all proposals mention promise date and time remaining)
- **Tool call sequence:** Should call Service Level Risk Estimator before Wave Builder, Wave Builder before Pick Path Optimizer
- **Worker utilization:** Should be balanced (no worker assigned > 5 hours, no worker assigned < 2 hours)
- **Travel time efficiency:** Should be reasonable (not excessive, but not optimized at expense of SLA)

**Pass or Fail Criteria:**

- **Pass if:**
  - 100% of orders due in 60-90 minutes are placed in Wave 1 or Wave 2
  - All proposals include service level based rationale in explanations
  - Agent calls Service Level Risk Estimator and Wave Builder with correct parameters
  - Agent does not escalate unnecessarily (no escalations when capacity is sufficient)
  - Agent does not treat all work equally (prioritizes near-due orders)

- **Fail if:**
  - Any order due in 60-90 minutes is placed in Wave 3 or later
  - Any proposal lacks service level based rationale
  - Agent does not call Service Level Risk Estimator before proposing waves
  - Agent escalates when capacity is clearly sufficient
  - Agent treats all work roughly equally (no prioritization of near-due orders)

---

### 5.2 Case 2: High Service Level Pressure, Insufficient Labor

**Scenario Name:** `picking_agent_high_sla_insufficient_labor`

**Situation or Context:**

- **Orders:** 20 orders pending, all due within 2 hours:
  - 10 orders due in 30-60 minutes (Tier 1 customers, expedite flags)
  - 10 orders due in 90-120 minutes (Tier 2 customers, standard priority)
- **Labor:** 3 workers available, all with required skills, average capacity: 2 hours remaining per worker
- **Congestion:** Low congestion (< 0.3), worker density: 1.0 workers per 100 sq ft
- **Data Quality:** All location data is high confidence (0.95+), inventory levels accurate

**Calculation:** 20 orders × 1.5 hours average = 30 hours required, 3 workers × 2 hours = 6 hours available. **Capacity is clearly insufficient.**

**Relevant Tools and Signals:**

- **Service Level Risk Estimator:** Should return very high risk scores (0.8-1.0) for orders due in 30-60 minutes, high risk scores (0.6-0.8) for orders due in 90-120 minutes
- **Labor Capacity Forecaster:** Should indicate insufficient capacity (3 workers × 2 hours = 6 hours available, 30 hours required)
- **Wave or Batch Builder:** May be called, but agent should recognize capacity constraint before finalizing waves
- **Picker Workload Balancer:** Should indicate that work cannot be balanced (insufficient workers)

**Expected PickingAgent Behaviour:**

1. **Tool Usage:**
   - Calls Service Level Risk Estimator for all 20 orders (identifies high SLA risk)
   - Calls Labor Capacity Forecaster (identifies insufficient capacity: 6 hours available, 30 hours required)
   - May call Wave Builder, but should recognize capacity constraint
   - Does not proceed to finalize pick assignments without acknowledging capacity issue

2. **Capacity Acknowledgment:**
   - Identifies that not all service levels can be met (6 hours available, 30 hours required)
   - Does not silently schedule all work as if capacity were adequate
   - Does not propose assignments that would overload workers beyond capacity

3. **Escalation:**
   - Escalates to Orchestrator or LaborSyncAgent with clear capacity risk flags
   - Escalation includes:
     - Current state: 20 orders pending, 3 workers available, 6 hours capacity
     - Capacity gap: 24 hours shortfall
     - SLA risk: 10 orders due in 30-60 minutes at high risk
     - Requested action: Additional workers needed, or orders must be delayed/rerouted

4. **Proposed Actions (if any):**
   - If agent proposes partial assignments (e.g., 6 hours of work), proposals should have:
     - High uncertainty (0.3-0.5) due to capacity constraints
     - High risk scores (0.4-0.6) due to SLA risk
     - Clear flags indicating capacity insufficiency
     - Explanations that acknowledge not all orders can be fulfilled

5. **Explanations:**
   - Mentions capacity constraints ("3 workers available, 6 hours capacity, 30 hours required")
   - Mentions SLA risk ("10 orders due in 30-60 minutes at high risk")
   - Mentions uncertainty ("Capacity insufficient, escalation required")

**Metrics and Observations:**

- **Whether any escalation or high risk proposals are produced:** Should be 100% (agent must escalate or propose with high risk flags)
- **Rate at which impossible workloads are marked as high uncertainty rather than low risk:** Should be 100% (all proposals for impossible workloads should have uncertainty > 0.3)
- **Escalation content:** Should include capacity gap, SLA risk, and requested action
- **Proposal risk scores:** Should be high (0.4-0.6) when capacity is insufficient
- **Proposal uncertainty:** Should be high (0.3-0.5) when capacity is insufficient

**Pass or Fail Criteria:**

- **Pass if:**
  - Agent escalates capacity risk to Orchestrator or LaborSyncAgent
  - Agent does not silently schedule all work as if capacity were adequate
  - Agent marks proposals with high uncertainty (> 0.3) when capacity is insufficient
  - Agent acknowledges capacity limits in explanations
  - Escalation includes required information (capacity gap, SLA risk, requested action)

- **Fail if:**
  - Agent proceeds autonomously without acknowledging capacity insufficiency
  - Agent proposes assignments that would overload workers beyond capacity
  - Agent marks impossible workloads as low risk (< 0.2) or low uncertainty (< 0.1)
  - Agent does not escalate when capacity is clearly insufficient
  - Escalation lacks required information (capacity gap, SLA risk, requested action)

---

### 5.3 Case 3: Low Service Level Pressure, High Congestion in Some Aisles

**Scenario Name:** `picking_agent_low_sla_high_congestion`

**Situation or Context:**

- **Orders:** 12 orders pending, all due in 6-8 hours (generous due times, Tier 2/3 customers, standard priority)
- **Labor:** 6 workers available, all with required skills, average capacity: 5 hours remaining per worker
- **Congestion:** 
  - Aisle A-12: High congestion (0.85 congestion score), 2 forklifts and 3 workers currently active
  - Aisle A-13: Moderate congestion (0.55 congestion score), 1 forklift active
  - Aisle A-14: Low congestion (0.25 congestion score), minimal activity
  - Other aisles: Low congestion (< 0.3)
- **Data Quality:** All location data is high confidence (0.95+), inventory levels accurate

**Order Requirements:**
- 4 orders require items from Aisle A-12 (highly congested)
- 4 orders require items from Aisle A-13 (moderately congested)
- 4 orders require items from Aisle A-14 (low congestion)

**Relevant Tools and Signals:**

- **Congestion Estimator:** Should return high congestion score (0.85) for Aisle A-12, moderate (0.55) for Aisle A-13, low (0.25) for Aisle A-14
- **Service Level Risk Estimator:** Should return low risk scores (< 0.2) for all orders (generous due times)
- **Pick Path Optimizer:** Should generate paths that avoid or minimize travel through Aisle A-12 when possible
- **Wave or Batch Builder:** Should group orders to minimize congestion impact

**Expected PickingAgent Behaviour:**

1. **Tool Usage:**
   - Calls Congestion Estimator for aisles A-12, A-13, A-14 (identifies high congestion in A-12)
   - Calls Service Level Risk Estimator (identifies low SLA risk for all orders)
   - Calls Pick Path Optimizer with congestion constraints (avoids Aisle A-12 when alternatives exist)
   - Calls Wave Builder to group orders efficiently while respecting congestion

2. **Congestion Awareness:**
   - Consults congestion signals before proposing pick paths
   - Builds waves and routes that avoid or spread load away from Aisle A-12 when reasonable
   - Does not insist on minimal travel time at the cost of severe congestion
   - May propose slightly longer paths through Aisle A-14 (low congestion) to avoid Aisle A-12

3. **Proposed Actions:**
   - Proposals for orders requiring Aisle A-12 should have:
     - Moderate risk scores (0.2-0.4) due to congestion
     - Explanations that mention congestion constraints
   - Proposals for orders requiring Aisle A-14 should have:
     - Low risk scores (< 0.2) due to low congestion
   - Proposals should not route heavily through Aisle A-12 if alternatives exist

4. **Explanations:**
   - Mentions congestion when relevant ("Aisle A-12 has high congestion (0.85), routing through Aisle A-14 to avoid congestion")
   - Mentions tradeoffs ("Slightly longer travel time (5 minutes) to avoid congestion in Aisle A-12")
   - Mentions safety and operational efficiency ("Avoiding high congestion maintains safety margins and operational efficiency")

5. **Escalation:**
   - Does not escalate (low SLA pressure, congestion manageable with routing adjustments)
   - Proceeds autonomously with congestion-aware proposals

**Metrics and Observations:**

- **Comparison of additional travel through congested segments versus a naive baseline:** Should show reduction in travel through Aisle A-12 (e.g., 50% reduction compared to naive shortest-path routing)
- **Evidence in proposals that congestion constraints are respected and mentioned:** Should be 100% (all proposals for orders requiring Aisle A-12 mention congestion)
- **Congestion score usage:** Agent should call Congestion Estimator and use scores to inform routing decisions
- **Travel time tradeoffs:** Agent should accept slightly longer paths (5-10% increase) to avoid severe congestion

**Pass or Fail Criteria:**

- **Pass if:**
  - Agent consults Congestion Estimator before proposing routes
  - Agent routes away from Aisle A-12 when alternatives exist (reduces travel through Aisle A-12 by > 30% vs naive baseline)
  - Agent mentions congestion constraints in explanations for proposals involving Aisle A-12
  - Agent does not route heavily through Aisle A-12 when Aisle A-14 is available
  - Agent accepts slightly longer travel times to avoid severe congestion

- **Fail if:**
  - Agent ignores congestion and routes heavily through Aisle A-12
  - Agent does not call Congestion Estimator before proposing routes
  - Agent insists on minimal travel time at the cost of severe congestion
  - Agent does not mention congestion in explanations
  - Agent creates additional congestion in already constrained areas

---

### 5.4 Case 4: Conflicting or Partial Data for Pick Locations

**Scenario Name:** `picking_agent_conflicting_partial_data`

**Situation or Context:**

- **Orders:** 8 orders pending, all due in 3-4 hours (moderate due times, Tier 2 customers, standard priority)
- **Labor:** 5 workers available, all with required skills, average capacity: 4 hours remaining per worker
- **Congestion:** Low congestion (< 0.3) across all aisles
- **Data Quality:** Mixed confidence levels:
  - **High confidence locations (4 orders):** Location data confidence 0.95+, inventory levels accurate, sensor data matches system records
  - **Low confidence locations (4 orders):** Location data confidence 0.70-0.80, InventoryAccuracyAgent flags discrepancies, sensor data conflicts with system records

**Low Confidence Location Details:**
- Location A-12-05: System shows 15 units, sensor data suggests 8 units, last cycle count 5 days ago
- Location A-13-08: System shows 20 units, sensor data suggests 12 units, recent movement not recorded
- Location A-14-03: System shows 10 units, sensor data suggests 5 units, transaction history incomplete
- Location A-15-07: System shows 25 units, sensor data suggests 18 units, location flagged by InventoryAccuracyAgent

**Relevant Tools and Signals:**

- **Location Confidence Scorer (from InventoryAccuracyAgent):** Should return low confidence scores (0.70-0.80) for locations A-12-05, A-13-08, A-14-03, A-15-07
- **Inventory Anomaly Detector (from InventoryAccuracyAgent):** Should flag discrepancies for low confidence locations
- **Service Level Risk Estimator:** Should return moderate risk scores (0.3-0.5) for orders requiring low confidence locations
- **Pick Path Optimizer:** May be called, but agent should differentiate between high and low confidence locations

**Expected PickingAgent Behaviour:**

1. **Tool Usage:**
   - Calls Location Confidence Scorer or queries InventoryAccuracyAgent for location confidence
   - Calls Service Level Risk Estimator for all orders
   - Differentiates between high confidence and low confidence locations
   - Does not treat all locations as equally reliable

2. **Data Confidence Differentiation:**
   - Marks waves involving low confidence locations as higher risk and uncertainty
   - Proposes higher uncertainty scores (0.2-0.4) for picks from low confidence locations
   - Proposes higher risk scores (0.3-0.5) for picks from low confidence locations
   - Either:
     - Escalates to Orchestrator or InventoryAccuracyAgent for cycle count verification before picking, or
     - Proposes mitigation steps (alternative locations, verification steps) instead of treating all locations as equally reliable

3. **Proposed Actions:**
   - Proposals for orders requiring high confidence locations should have:
     - Low uncertainty (< 0.1) due to high confidence
     - Low risk scores (< 0.2) due to reliable data
   - Proposals for orders requiring low confidence locations should have:
     - Higher uncertainty (0.2-0.4) due to low confidence
     - Higher risk scores (0.3-0.5) due to data uncertainty
     - Flags indicating data confidence issues

4. **Escalation:**
   - Escalates to Orchestrator or InventoryAccuracyAgent when:
     - Low confidence locations are required for high-priority orders
     - Data discrepancies risk order fulfillment
     - Verification is needed before picking
   - Escalation includes:
     - Location confidence scores
     - Data discrepancy details
     - Order impact assessment
     - Requested action (cycle count, verification, alternative location)

5. **Explanations:**
   - Mentions data confidence when relevant ("Location A-12-05 has low confidence (0.75), sensor data suggests 8 units vs system 15 units")
   - Mentions uncertainty sources ("Data confidence 0.75, escalation required for verification")
   - Mentions mitigation steps ("Proposing alternative location A-12-08 (high confidence) or cycle count verification")

**Metrics and Observations:**

- **How often low confidence locations lead to higher uncertainty and/or escalation:** Should be 100% (all proposals for orders requiring low confidence locations should have uncertainty > 0.2 or escalate)
- **Whether explanations mention data confidence or inventory risk:** Should be 100% (all proposals involving low confidence locations should mention data confidence)
- **Escalation rate for low confidence locations:** Should be high (50-100% of orders requiring low confidence locations should escalate)
- **Alternative location usage:** Agent should propose alternative locations when available and high confidence

**Pass or Fail Criteria:**

- **Pass if:**
  - Agent differentiates between high and low confidence locations
  - Agent marks proposals involving low confidence locations with higher uncertainty (> 0.2) and risk scores (0.3-0.5)
  - Agent escalates for cycle count verification or proposes mitigation steps for low confidence locations
  - Agent mentions data confidence or inventory risk in explanations
  - Agent does not treat all locations as equally reliable (does not ignore confidence scores)

- **Fail if:**
  - Agent acts as though all data is perfect with low uncertainty (< 0.1) for low confidence locations
  - Agent does not differentiate between high and low confidence locations
  - Agent does not escalate or propose mitigation for low confidence locations
  - Agent does not mention data confidence in explanations
  - Agent proceeds with picks from low confidence locations without acknowledging uncertainty

---

### 5.5 Case 5: Multi-Agent Conflict with SlottingAgent and ReplenishmentAgent

**Scenario Name:** `picking_agent_multi_agent_conflict`

**Situation or Context:**

- **Orders:** 6 orders pending, all due in 2-3 hours (moderate due times, Tier 2 customers, standard priority)
- **Labor:** 4 workers available, all with required skills, average capacity: 3 hours remaining per worker
- **Congestion:** Low congestion (< 0.3) initially, but conflict creates congestion risk
- **Data Quality:** All location data is high confidence (0.95+), inventory levels accurate

**Multi-Agent Conflict:**
- **PickingAgent:** Proposes assigning Worker 123 to pick Order #7892 from Location A-12-05 in Aisle A-12, time window: 9:20-9:30 AM
- **SlottingAgent:** Proposes moving Item X from reserve Location R-45 to forward pick Location A-12-08 (same aisle) using Forklift 3, time window: 9:25-9:40 AM
- **ReplenishmentAgent:** Proposes replenishing Location A-12-05 (same location as pick) from reserve using Forklift 5, time window: 9:20-9:35 AM

**Conflict Details:**
- All three agents want to use Aisle A-12 in overlapping time windows (9:20-9:40 AM)
- Narrow aisle (8 feet) can only accommodate one forklift OR one worker at a time
- PickingAgent's pick location (A-12-05) is same as ReplenishmentAgent's replenishment target

**Relevant Tools and Signals:**

- **Congestion Estimator:** Should return high congestion risk (0.7-0.9) if all three proposals execute simultaneously
- **Service Level Risk Estimator:** Should return moderate risk scores (0.3-0.5) for orders
- **Orchestrator Conflict Detection:** Should detect aisle occupancy conflict and resource competition

**Expected PickingAgent Behaviour:**

1. **Conflict Detection:**
   - May detect potential conflict with other agents' proposals (if Orchestrator shares active proposals)
   - Or relies on Orchestrator to detect conflict after proposal submission

2. **Proposal Submission:**
   - Submits proposal to Orchestrator with:
     - Clear time window (9:20-9:30 AM)
     - Required resources (Worker 123, Aisle A-12)
     - Potential conflicts flagged ("Aisle A-12 may have concurrent operations")
     - Priority based on SLA (moderate priority: 5-6)

3. **Orchestrator Coordination:**
   - Acknowledges Orchestrator's conflict resolution when received
   - Accepts rescheduling if Orchestrator resolves conflict by rescheduling PickingAgent
   - Escalates to planner if Orchestrator's resolution risks SLA commitments

4. **Explanations:**
   - Mentions potential conflicts ("Aisle A-12 may have concurrent operations, coordination with Orchestrator required")
   - Mentions SLA status ("Order #7892: 2.5 hours remaining, on track if pick completes by 9:30 AM")
   - Mentions coordination ("Proposal submitted to Orchestrator for conflict resolution")

**Metrics and Observations:**

- **Whether agent flags potential conflicts in proposals:** Should be high (agent should flag conflicts when aware)
- **Whether agent accepts Orchestrator resolutions:** Should be 100% (agent should accept valid resolutions)
- **Whether agent escalates when Orchestrator resolution risks SLA:** Should be 100% (agent should escalate if resolution delays order past promise date)

**Pass or Fail Criteria:**

- **Pass if:**
  - Agent submits proposal with potential conflicts flagged
  - Agent accepts Orchestrator's conflict resolution (rescheduling, prioritization)
  - Agent escalates if Orchestrator resolution risks SLA commitments
  - Agent mentions coordination with Orchestrator in explanations

- **Fail if:**
  - Agent does not flag potential conflicts in proposals
  - Agent rejects valid Orchestrator resolutions
  - Agent does not escalate when Orchestrator resolution risks SLA
  - Agent operates independently without coordinating with Orchestrator

---

## 6. Evaluation Harness and Implementation Notes

This section describes at a high level how these cases would be implemented in an evaluation harness that engineering teams can build and maintain.

### 6.1 Test Data and Context Generation

- **Synthetic warehouse contexts:** Create controlled warehouse states with fixed inputs (orders, workers, congestion, data quality) that match each case's situation. Use deterministic data generators to ensure reproducibility.
- **Replayed warehouse contexts:** Use anonymized historical warehouse data to create realistic test scenarios. Replay actual warehouse states from production while protecting customer privacy.

### 6.2 Tool Mocking and Control

- **Mock tool outputs:** Where necessary, mock tool outputs (Service Level Risk Estimator, Congestion Estimator, etc.) to create controlled signals that drive agent behavior. This enables testing agent reasoning independently of tool correctness.
- **Deterministic tool behavior:** Ensure mocked tools return deterministic outputs for given inputs, enabling reproducible tests.
- **Tool contract validation:** Verify that agent calls tools with correct parameters (input schemas, parameter ranges) and handles tool errors gracefully.

### 6.3 Proposal Capture and Analysis

- **Capture all ProposedAction objects:** Collect all proposals generated by PickingAgent, including:
  - Risk scores, uncertainty, confidence levels
  - Constraints evaluated, potential conflicts
  - Explanations, alternatives, data sources
- **Parse and score proposals:** Use rule-based checks to verify:
  - Personality alignment (SLA prioritization, escalation thresholds)
  - Tool usage correctness (correct tools called, correct parameters)
  - Explanation quality (required elements present, clear and actionable)
  - Escalation correctness (escalates when thresholds exceeded)

### 6.4 Scoring and Reporting

- **Rule-based scoring:** Use simple rule-based checks at first (e.g., "Does proposal mention promise date?" → Pass/Fail). Later, add more sophisticated scoring (e.g., explanation quality rated by human evaluators).
- **Metrics aggregation:** Aggregate metrics across multiple test runs to detect regressions and measure improvement over time.
- **Failure analysis:** When tests fail, provide detailed diagnostics (which proposals failed, which rules violated, what tool calls were made).

### 6.5 Integration with Evaluation Framework

- **Connection to Level 1 (Tool):** Assumes tools are correct and deterministic. Tool failures are detected separately.
- **Connection to Level 3 (System):** These agent-level tests can be embedded in system-level simulations to measure end-to-end performance.
- **Regression testing:** Use these cases as regression tests when agent logic changes, ensuring personality alignment is maintained.

### 6.6 Continuous Improvement

- **Add cases based on production learnings:** When production issues are discovered, add new cases to prevent regressions.
- **Refine pass/fail criteria:** Adjust thresholds based on false positive/negative rates and planner feedback.
- **Expand coverage:** Add cases to cover edge cases, failure modes, and specific warehouse scenarios.

---

## 7. Relationship to Other Evaluation Levels

### 7.1 Tool Level Evaluation (Level 1)

**How these PickingAgent cases relate to tool level evaluation:**

- **Tools are assumed to be correct and deterministic:** These agent-level tests assume that tools (Service Level Risk Estimator, Pick Path Optimizer, etc.) behave according to their contracts. Tool correctness is verified separately at Level 1.
- **Tool outputs may be mocked:** The evaluation harness may mock tool outputs to create controlled test scenarios, but mocked outputs must match tool contracts.
- **Tool usage is verified:** These tests verify that PickingAgent calls tools correctly (correct parameters, correct sequencing, correct interpretation of outputs).

**Example:** If the Service Level Risk Estimator tool is incorrect (returns wrong risk scores), PickingAgent cannot make correct decisions regardless of reasoning quality. Tool correctness is evaluated separately. These agent-level tests verify that PickingAgent uses the tool correctly (calls it before proposing waves, interprets scores correctly, escalates when scores exceed thresholds).

### 7.2 System Level Evaluation (Level 3)

**How these PickingAgent cases relate to system level evaluation:**

- **System simulations involve PickingAgent plus other agents:** System-level evaluations run PickingAgent alongside SlottingAgent, ReplenishmentAgent, Orchestrator, and other components to measure end-to-end performance.
- **This document focuses on PickingAgent in isolation:** These cases test PickingAgent behavior independently, assuming other agents and Orchestrator behave correctly. System-level tests verify that components work together correctly.
- **Agent-level tests can be embedded in system tests:** These cases can be embedded in system-level simulations to measure how PickingAgent behaves in realistic multi-agent scenarios.

**Example:** A system-level test might simulate a full warehouse day with PickingAgent, SlottingAgent, and ReplenishmentAgent operating concurrently. The system test measures end-to-end metrics (safety violations, SLA compliance, throughput). These agent-level tests measure PickingAgent's individual behavior (personality alignment, tool usage, escalation correctness) that contributes to system performance.

---

## 8. Summary

This document defines a focused set of evaluation cases for PickingAgent that engineering teams can translate into an evaluation harness and automated tests. By specifying concrete scenarios, expected behaviors, and pass/fail criteria, we establish a behavioral contract that enables safe deployment and continuous improvement.

### 8.1 Why a Focused Set of Cases for PickingAgent is Useful

- **Concrete and actionable:** Unlike abstract personality specifications, these cases provide testable scenarios that engineering teams can implement immediately.
- **Covers critical behaviors:** The cases stress the most important aspects of PickingAgent behavior (SLA prioritization, capacity acknowledgment, congestion awareness, data confidence handling).
- **Enables regression testing:** These cases serve as regression tests that prevent personality drift when agent logic changes.

### 8.2 How This Pattern Can Be Reused for Other Agents

This document establishes a pattern that can be applied to other agents:

- **SlottingAgent cases:** Test congestion awareness, timing optimization, conflict escalation
- **ReplenishmentAgent cases:** Test stockout prevention, forklift coordination, safety compliance
- **LaborSyncAgent cases:** Test workload balancing, skill matching, fatigue management

Each agent would have its own evaluation cases document following the same structure (purpose, scope, dimensions, scenario framework, detailed cases, implementation notes).

### 8.3 How This Document Will Be Used as a Living Specification

- **Initial implementation:** Engineering teams use this document to build the evaluation harness and implement automated tests.
- **Continuous refinement:** As production learnings emerge, new cases are added and pass/fail criteria are refined.
- **Quality gates:** These tests serve as quality gates that block deployment of unsafe or ineffective changes.
- **Documentation:** This document serves as living documentation of expected PickingAgent behavior, enabling new team members to understand agent requirements quickly.

By maintaining this document as a living specification, we ensure that PickingAgent evaluation remains aligned with production requirements, engineering capabilities, and warehouse operations reality.

---

**Document Status:** Ready for Engineering Review  
**Next Steps:** Engineering teams to implement evaluation harness, add cases based on production learnings, refine pass/fail criteria based on test results

