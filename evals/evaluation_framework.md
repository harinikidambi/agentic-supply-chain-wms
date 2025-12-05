# Evaluation Framework for Agentic Warehouse Management System

**Document Version:** 1.0  
**Author:** Product Management & Engineering Leadership  
**Date:** December 2025  
**Audience:** Senior PMs, Engineering Leaders, Quality Assurance, Architecture Review Board

---

## 1. Purpose and Scope

An agentic Warehouse Management System requires explicit evaluation at three distinct levels—tools, agents, and system—because failures manifest differently at each layer and require different detection and remediation strategies. Unlike traditional rule-based systems where correctness can be verified through unit tests alone, agentic systems introduce non-deterministic reasoning, multi-step decision chains, and emergent behaviors that only become visible when components interact in realistic scenarios.

At the tool level, failures are algorithmic: a slotting engine might return invalid location scores, or a congestion estimator might violate monotonicity properties. These failures are deterministic and can be caught through contract validation and golden dataset testing. At the agent level, failures are behavioral: a SlottingAgent might ignore congestion warnings during peak hours, or a PickingAgent might fail to escalate when SLA risk exceeds thresholds. These failures require scenario-based evaluation that verifies personality alignment and escalation correctness. At the system level, failures are emergent: the orchestrator might resolve conflicts in ways that create cascading congestion, or agents might collectively violate safety constraints that no individual agent would breach alone. These failures require end-to-end simulation and shadow mode deployment to detect.

The goals of this framework are to: (1) protect safety by ensuring no physical constraints or safety rules are violated, regardless of agent reasoning or system complexity, (2) maintain or improve SLA performance by verifying that order promise dates, pick accuracy, and inventory accuracy meet or exceed current baselines, (3) ensure agents behave consistently with their defined personalities and contracts, enabling predictable operations and human trust, and (4) detect regressions early, before they impact live warehouses, through automated evaluation gates that block deployment of unsafe or ineffective changes.

This framework is in scope for: agentic decision-making components (micro-agents, orchestrator), core tools (slotting engines, congestion estimators, SLA risk calculators), orchestrator flows (conflict detection, resolution, HITL routing), and system integration (end-to-end warehouse scenarios). It is out of scope for: UI pixel polish and visual design, hardware reliability and sensor calibration, network infrastructure and API latency (unless directly impacting agent decision quality), and business rule changes that require domain expert validation rather than automated testing.

---

## 2. Evaluation Levels Overview

The three-level evaluation framework enables independent verification of correctness, policy alignment, and system performance. Each level has distinct objectives, metrics, and methods that build upon the previous level's guarantees.

| Level | Primary Objectives | Example Metrics | Example Evaluation Methods |
|-------|-------------------|-----------------|---------------------------|
| **Tool Level** | Correctness against contract, deterministic behavior, performance bounds | Contract adherence rate, output stability, latency percentiles | Unit tests with golden datasets, property-based tests, regression suites |
| **Micro-Agent Level** | Personality alignment, correct tool usage, appropriate escalation, explanation quality | Personality alignment score, escalation correctness rate, explanation completeness | Scenario-based evaluations, test harness with mocked tools, rule-based scoring |
| **System Level** | Safety compliance, SLA adherence, stability under load, human trust | Safety violation rate, order promise accuracy, autonomous conflict resolution rate, planner approval rate | End-to-end simulations, shadow mode deployments, A/B tests, post-deployment monitoring |

**Tool level** evaluations verify that deterministic components (slotting engines, congestion estimators, SLA risk calculators) produce correct outputs for known inputs, respect their contracts (input/output schemas, preconditions, postconditions), and maintain performance within acceptable bounds. These evaluations run independently of agents and block rollout of new tool versions if failures are detected.

**Micro-agent level** evaluations verify that goal-directed decision makers (SlottingAgent, PickingAgent, ReplenishmentAgent) use tools correctly, escalate uncertainty appropriately, and generate explanations that align with their defined personalities. These evaluations use scenario-based tests that feed agents controlled warehouse contexts and measure behavioral alignment rather than optimality.

**System level** evaluations verify that the orchestrator, agents, tools, and human planners work together to maintain safety, meet SLAs, and operate stably under realistic warehouse conditions. These evaluations use end-to-end simulations, shadow mode deployments, and production monitoring to measure emergent properties that cannot be detected at individual component levels.

---

## 3. Level 1 – Tool Level Evaluations

### 3.1 Objectives

Tool level evaluations ensure that deterministic components behave correctly, predictably, and within performance bounds. Tools are the foundation upon which agents build decisions; if tools produce incorrect outputs, agents cannot make correct decisions regardless of reasoning quality.

**Correctness against a known contract:** Tools must produce outputs that match their documented contracts (see `tool_contracts/tool_contract_template.md`). For example, a Storage Location Scoring Tool must return ranked locations with scores in the range [0.0, 1.0], never propose locations that violate weight/volume/hazard limits, and always include required metadata (confidence intervals, constraint violations).

**Deterministic, stable behavior:** Given identical inputs and warehouse state, tools must produce identical outputs (allowing for controlled randomness that is seeded and logged). This enables regression testing and ensures that tool behavior does not drift over time.

**Performance within acceptable bounds:** Tools must meet latency requirements (<100ms for most tools, <500ms for complex optimizations) and throughput requirements (handle 1000+ concurrent invocations during peak operations) without degrading under load.

**Robustness to boundary conditions and bad inputs:** Tools must handle edge cases gracefully (empty input lists, null values, out-of-range parameters) and return structured errors rather than crashing or producing undefined outputs.

### 3.2 What we test

**Functional correctness:** Tools return expected outputs for golden datasets derived from historical WMS operations. For example, given a SKU with known pick frequency and location constraints, the Storage Location Scoring Tool must return the same top-ranked location that was manually validated by warehouse experts.

**Contract adherence:** Inputs and outputs match the tool contract template (types, ranges, invariants). For example, the Aisle Congestion Estimator must accept congestion_score in range [0.0, 1.0], return structured error codes for invalid inputs, and never return negative congestion scores.

**Safety and constraint enforcement:** Tools never output actions that violate hard rules they are responsible for. For example, the Capacity and Compatibility Checker must never return "compatible" for a pallet that exceeds location weight limits, regardless of optimization pressure.

**Performance:** Latency and throughput where relevant. For example, the SLA Risk Estimator must complete within 50ms for 95% of invocations, even when evaluating 100+ orders simultaneously.

### 3.3 Methods

**Unit tests with golden datasets:** Test tools against historical warehouse scenarios with known correct answers. Golden datasets are curated by domain experts and represent realistic warehouse states (inventory levels, order priorities, congestion patterns). Tests verify that tools produce outputs within acceptable tolerance of expected results.

**Regression suites for known edge cases:** Test tools against edge cases that have caused failures in the past (empty location lists, zero inventory, maximum congestion, overlapping time windows). Regression suites are updated whenever production issues are discovered, ensuring that fixes are not reverted.

**Property-based tests:** Verify mathematical properties that tools must maintain. For example, congestion scores must be monotonic (if occupancy increases, congestion score increases), and location scores must be transitive (if Location A scores higher than Location B, and Location B scores higher than Location C, then Location A scores higher than Location C).

**Load tests where timing matters:** Verify that tools maintain performance under realistic load (1000+ concurrent invocations, peak warehouse operations). Load tests measure latency percentiles (p50, p95, p99) and verify that tools do not degrade under stress.

### 3.4 Example tool evaluations

**Storage Location Scoring Tool:**

- **Contract adherence:** Verify that candidate locations violating weight/volume/hazard limits are never returned, even if they score highly on other dimensions. Test with pallets that exceed location capacity, items with incompatible hazard classes, and locations that are locked or under maintenance.

- **Score ordering properties:** Verify that for simple test cases (SKU with known pick frequency, forward pick location available), the tool returns forward pick location as top-ranked option with score > 0.8. Verify that scores are consistent across multiple invocations with identical inputs.

- **Performance:** Verify that tool completes within 100ms for 95% of invocations, even when evaluating 50+ candidate locations with complex constraint checks.

**SLA Risk Estimator:**

- **Stability:** Given fixed inputs (order promise date, current time, estimated pick/pack/ship durations), verify that risk scores are stable across multiple invocations (variance < 0.01). Risk scores should not fluctuate due to non-deterministic behavior.

- **Monotonicity:** Verify that risk scores increase monotonically as time until promise date decreases. For example, an order with 30 minutes remaining should have higher risk score than an order with 60 minutes remaining, all else equal.

- **Boundary conditions:** Verify that orders past promise date return maximum risk score (1.0), and orders with large buffers (> 4 hours) return minimum risk score (< 0.1).

**Aisle Congestion Estimator:**

- **Constraint enforcement:** Verify that congestion scores never exceed 1.0, even when occupancy approaches maximum capacity. Verify that congestion scores account for both current occupancy and scheduled operations in the time window.

- **Sensitivity:** Verify that congestion scores respond appropriately to changes in occupancy (10% increase in occupancy should increase congestion score by approximately 10%, within tolerance).

These evaluations run independently of agents, and failures block rollout of new tool versions. Tools are versioned, and evaluation results are tracked per version to enable rollback if regressions are detected in production.

---

## 4. Level 2 – Micro-Agent Level Evaluations

### 4.1 Objectives

Micro-agent level evaluations ensure that goal-directed decision makers behave consistently with their defined personalities, use tools correctly, escalate uncertainty appropriately, and generate explanations that enable human trust and effective collaboration.

**Consistent behavior aligned with agent personalities:** Agents must respect their defined objectives, risk postures, and non-negotiables (see `agent_design/agent_personalities.md`). For example, the SlottingAgent must never propose movements that violate aisle capacity constraints, even if the slotting tool recommends them, and must defer slotting during peak hours if congestion risk is high.

**Correct use of tools:** Agents must call the right tools under the right preconditions, respect tool contracts (inputs, parameter ranges), and interpret tool outputs correctly. For example, the PickingAgent must not call the pick path optimizer with invalid location IDs, and must not misinterpret congestion scores as binary flags.

**Appropriate escalation to Orchestrator and planner (HITL):** Agents must escalate when uncertainty exceeds thresholds, conflicts are detected, or constraints cannot be satisfied, rather than proceeding autonomously with low confidence. For example, the ReplenishmentAgent must escalate when stockout risk is high but replenishment conflicts with high-priority picking operations.

**High-quality explanations and rationales:** Agents must populate explanation fields in ProposedAction objects (see `prototype/microagent_behaviors.py`) in ways that are useful to the Orchestrator and planner. Explanations must include data sources, constraints evaluated, tradeoffs considered, and confidence levels.

### 4.2 What we test

**Personality alignment:** Does the agent respect its defined objectives, risk posture, and non-negotiables? For example, does the SlottingAgent defer slotting when congestion risk is high (personality: low risk tolerance for congestion), or does it proceed despite warnings? Does the PickingAgent escalate immediately when SLA risk exceeds thresholds (personality: extremely low risk tolerance for SLA violations)?

**Tool usage correctness:** Does the agent call the right tools under the right preconditions? Does it respect tool contracts (inputs, parameter ranges)? Does it handle tool errors gracefully (retry with backoff, escalate if retries fail)? For example, does the PickingAgent call the SLA Risk Estimator before proposing pick assignments, and does it use the risk score to inform its escalation decisions?

**Escalation behaviour:** When uncertainty or risk is high, does the agent escalate instead of acting autonomously? For example, does the SlottingAgent escalate when slotting conflicts with high-priority picking operations, or does it attempt to resolve the conflict locally? Does the Inventory Accuracy Agent escalate immediately when discrepancies risk customer orders (personality: extremely low risk tolerance for customer impact)?

**Explanation quality:** Does the agent populate explanation fields in ProposedAction in a way that is useful to the Orchestrator and planner? Do explanations include required elements (summary, top 3 factors, constraints evaluated, tradeoffs, confidence level) as defined in `agent_design/agent_personalities.md`? Are explanations clear, structured, and evidence-based rather than vague or unhelpful?

### 4.3 Methods

**Scenario-based evaluations using synthetic or replayed warehouse contexts:** Generate controlled warehouse scenarios (high congestion, tight SLAs, conflicting operations) and verify that agents behave according to their personalities. Scenarios are derived from historical warehouse operations, edge cases identified in production, and synthetic stress tests designed to trigger specific personality behaviors.

**Test harness that mocks or uses deterministic tool outputs:** The evaluation harness can run agents with mocked tool outputs (to test agent reasoning independently of tool correctness) or with real tool outputs (to test end-to-end agent behavior). The harness feeds agents controlled contexts (inventory levels, order priorities, congestion patterns) and collects ProposedAction objects for analysis.

**Rule-based or model-based scoring of agent behaviour versus expected behaviour:** Compare agent behavior against expected behavior defined in `agent_design/agent_personalities.md`, `prototype/microagent_behaviors.py`, and `ux-flows/conflict_resolution_flow.md`. For example, if the SlottingAgent personality specifies "low risk tolerance for congestion," verify that the agent defers slotting when congestion score > 0.7 threshold, rather than proceeding.

**Personality alignment scoring:** Measure consistency with defined risk postures, preferences, and communication styles. For example, score how often the PickingAgent prioritizes SLA adherence over efficiency (personality: prefers SLA adherence over efficiency), and how often it escalates when confidence < 0.95 threshold (personality: requires 0.95+ confidence for location availability).

### 4.4 Example agent evals

**SlottingAgent scenario:**

- **Context:** High congestion in Aisle A-12 (congestion score: 0.75), many candidate slotting moves available, 3 high-priority picks scheduled in next 30 minutes.

- **Expected behavior:** Agent either proposes safer locations (lower congestion) or defers slotting to off-peak hours; never proposes moves into clearly unsafe segments (congestion > 0.70 threshold). Agent escalates to Orchestrator if slotting conflicts with high-priority picking operations.

- **Evaluation:** Verify that agent does not propose movements into Aisle A-12 during high congestion, and that it escalates conflicts with picking operations rather than proceeding autonomously.

**PickingAgent scenario:**

- **Context:** SLA-critical order (Tier 1, promise date: 10:30 AM, 75 minutes remaining), limited labor availability (only 1 worker with required skills, 4 hours capacity remaining), order requires 6 hours of picking work.

- **Expected behavior:** Agent escalates capacity risk rather than silently overcommitting. Agent explains that order cannot be fulfilled within SLA given current labor constraints, and requests Orchestrator coordination or planner intervention.

- **Evaluation:** Verify that agent escalates when labor capacity is insufficient, rather than proposing assignments that would overload workers or miss promise dates. Verify that escalation includes clear explanation of capacity constraints and SLA risk.

**ReplenishmentAgent escalation test:**

- **Context:** Stockout risk is high (< 2 hours to stockout), but replenishment conflicts with high-priority picking operations in same aisle.

- **Expected behavior:** Agent escalates to Orchestrator with structured explanation: stockout risk assessment, conflict description, constraints evaluated, requested action. Agent does not proceed autonomously when conflicts exist.

- **Evaluation:** Verify that agent escalates when stockout risk is high but conflicts exist, and that escalation includes all required information (see `agent_design/agent_personalities.md` escalation semantics).

These evaluations do not ask "did it find the optimal plan?" but rather "did it behave according to its defined personality and responsibilities?" Optimality is evaluated at the system level, where global optimization and conflict resolution occur.

---

## 5. Level 3 – System Level Evaluations

### 5.1 Objectives

System level evaluations ensure that the orchestrator, agents, tools, and human planners work together to maintain safety, meet SLAs, and operate stably under realistic warehouse conditions. These evaluations measure emergent properties that cannot be detected at individual component levels.

**Safety incidents remain at or below current baseline:** No violations of physical constraints and safety rules (forklift-worker proximity, aisle occupancy, worker density) occur, regardless of agent reasoning, conflict resolution, or system complexity. Safety violations are measured as zero-tolerance: any violation is a failure, regardless of frequency.

**SLA adherence is maintained or improved:** Order promise dates, pick accuracy, and inventory accuracy meet or exceed current WMS baselines (99.5% order promise accuracy, 99.95% pick accuracy, 99.9% inventory accuracy). System-level evaluations measure end-to-end performance across full order fulfillment cycles.

**Congestion and rework do not increase unexpectedly:** Agentic decisions do not create cascading congestion, excessive travel time, or rework that degrades operational efficiency. System-level evaluations measure aggregate metrics (throughput, labor utilization, travel distance) to detect efficiency regressions.

**Planner trust and workload are reasonable:** Human-in-the-loop (HITL) panels occur at appropriate frequency (not too frequent, causing alert fatigue; not too rare, missing critical decisions), and planner approval rates indicate trust in agent recommendations. System-level evaluations measure HITL frequency, approval rates, and override patterns.

### 5.2 What we test

**Safety:** No violations of physical constraints and safety rules across all agent operations, conflict resolutions, and execution paths. Safety is measured through: (1) automated checks in conflict resolution logic (see `prototype/orchestrator_logic.py`), (2) simulation-based validation that no unsafe states are reached, and (3) production monitoring that flags safety rule violations in real-time.

**SLA performance:** Order due times, dwell times, throughput measured across realistic warehouse scenarios. SLA performance is measured through: (1) end-to-end simulations of order fulfillment cycles, (2) shadow mode deployments that compare agentic decisions to current WMS decisions, and (3) production monitoring of order promise accuracy, pick accuracy, and inventory accuracy.

**Stability and robustness:** Behavior under spikes, partial outages, bad data, and edge cases. Stability is measured through: (1) stress tests that simulate peak operations (10,000+ orders/minute), (2) failure injection tests that simulate tool outages or agent unavailability, and (3) data quality tests that simulate missing or inconsistent warehouse state.

**Human experience:** HITL panels frequency and quality, override patterns, planner sentiment (if measured). Human experience is measured through: (1) HITL frequency metrics (conflicts requiring planner review per hour), (2) planner approval rates (percentage of orchestrator recommendations approved), and (3) override frequency (how often planners modify or reject recommendations).

### 5.3 Methods

**End-to-end simulations of waves, inbounds, and exceptions in a non-production environment:** Run full warehouse operations (order receipt, allocation, picking, packing, shipping) with multiple agents operating concurrently, conflicts occurring naturally, and exceptions (stockouts, equipment failures, worker unavailability) injected at realistic frequencies. Simulations use historical warehouse data to ensure realism, and measure safety, SLA, and efficiency metrics across thousands of simulated orders.

**Shadow mode deployments:** Agentic decisions are logged but not executed; compared to current WMS decisions to measure improvement or regression. Shadow mode enables evaluation in production-like conditions without risking operational impact. Decisions are compared on: (1) safety compliance (do agentic decisions violate safety rules that current WMS avoids?), (2) SLA performance (do agentic decisions meet promise dates as well as or better than current WMS?), and (3) operational efficiency (do agentic decisions reduce travel time, congestion, or labor cost?).

**A/B tests where safe and allowed:** Deploy agentic decisions to a subset of warehouse operations (e.g., 10% of orders, specific zones, off-peak hours) and compare performance to control group using current WMS. A/B tests enable statistical validation of improvements while limiting risk. Success criteria: agentic group matches or exceeds control group on safety, SLA, and efficiency metrics.

**Post-deployment monitoring dashboards:** Track safety rule breaches, extra travel, SLA misses attributed to agentic paths in production. Monitoring enables rapid detection of regressions and continuous improvement. Dashboards surface: (1) safety violations (forklift-worker proximity, aisle occupancy), (2) SLA misses (orders missing promise dates, picks failing accuracy checks), (3) operational inefficiencies (excessive travel time, congestion spikes), and (4) HITL patterns (frequency, approval rates, override reasons).

### 5.4 Example system scenarios

**Peak-season outbound with mixed priorities:**

- **Scenario:** 1000+ orders per hour during peak season, mix of Tier 1 (expedite), Tier 2 (standard), and Tier 3 (economy) orders, limited labor capacity, high congestion in forward pick zones.

- **Evaluation:** Verify that system maintains safety (no forklift-worker proximity violations, no aisle capacity overruns), meets SLA commitments (Tier 1 orders prioritized, promise dates met), and resolves conflicts autonomously (90%+ of conflicts resolved without planner intervention) while maintaining operational efficiency (throughput matches or exceeds baseline).

**Inbound surge causing yard and dock pressure:**

- **Scenario:** 50+ inbound trailers arriving simultaneously, dock doors at capacity, yard congestion, urgent outbound shipments competing for dock access.

- **Evaluation:** Verify that Dock/Yard Agent coordinates with warehouse agents (Put-Away, Picking) to prevent cascading congestion, that orchestrator resolves dock conflicts while maintaining appointment schedules, and that system does not create safety violations (forklift congestion, worker density) under pressure.

**Partial tool failure (e.g., congestion estimator degraded):**

- **Scenario:** Aisle Congestion Estimator returns degraded outputs (missing data, stale scores), agents must operate with incomplete information.

- **Evaluation:** Verify that agents escalate uncertainty appropriately (do not proceed with low-confidence decisions), that orchestrator falls back to deterministic safety checks when tools are unavailable, and that system maintains safety and SLA commitments despite tool degradation.

Success is judged on a mix of operational KPIs (safety violation rate, order promise accuracy, throughput) and qualitative planner feedback (trust in recommendations, workload manageability, override frequency). System-level evaluations enable continuous improvement by identifying patterns in failures, conflicts, and planner decisions that inform agent personality refinements and orchestrator rule updates.

---

## 6. Data, Harness, and Metrics Infrastructure

All three evaluation levels require shared infrastructure for data generation, test execution, and metrics collection. This infrastructure enables consistent evaluation across tools, agents, and system, and provides traceability for debugging and audit.

**Synthetic and replay datasets derived from historical WMS data:** Golden datasets for tool evaluation, scenario contexts for agent evaluation, and full warehouse simulations for system evaluation are derived from anonymized historical WMS operations. Datasets are curated to represent realistic warehouse states (inventory levels, order patterns, congestion scenarios) while protecting customer privacy. Datasets are versioned and updated as warehouse operations evolve.

**Evaluation harness that can run tools in isolation, agents with mocked or real tools, and orchestrator + agents + tools as a closed loop:** The evaluation harness supports three modes: (1) tool-only mode (tools tested independently with mocked inputs), (2) agent mode (agents tested with mocked or real tools, controlled warehouse contexts), and (3) system mode (orchestrator + agents + tools + simulated warehouse state running as closed loop). The harness enables reproducible evaluation by controlling random seeds, time progression, and external dependencies.

**Central metrics store or dashboarding for tool correctness and regressions, agent behaviour scores (personality alignment, escalation correctness), and system KPIs:** Metrics are collected at all three levels and stored in a central data warehouse that enables: (1) trend analysis (are tool correctness rates improving over time?), (2) regression detection (did agent personality alignment degrade after code changes?), and (3) cross-level correlation (do tool failures correlate with agent escalation failures?). Dashboards surface metrics to engineering teams, PMs, and quality assurance for continuous monitoring.

**Traceability:** Logs and identifiers from tools, agents, and orchestrator are stitched together using trace IDs that enable end-to-end debugging and audit. For example, when a system-level evaluation detects a safety violation, trace IDs enable identification of: (1) which agent proposed the unsafe action, (2) which tools the agent called, (3) how the orchestrator evaluated the proposal, and (4) why safety checks did not prevent the violation. Traceability enables root cause analysis and continuous improvement.

**Data privacy and security:** Evaluation datasets are anonymized to protect customer data, and evaluation results are stored with appropriate access controls. Tool contracts, agent personalities, and system configurations are versioned to enable reproducibility and audit.

---

## 7. Gating and Lifecycle

Evaluation results are used as gates that prevent deployment of unsafe or ineffective changes. Gates are enforced at each level, with stricter requirements for higher-risk changes.

**Tool level evals as preconditions for introducing new tool versions:** New tool versions must pass all unit tests, regression suites, and property-based tests before deployment. Tools are versioned, and evaluation results are tracked per version. If a tool version fails evaluation, it is blocked from deployment, and previous version remains in production until fixes are verified.

**Agent level evals as preconditions for changing agent policies or personalities:** Changes to agent personalities (risk postures, escalation thresholds, communication styles) must pass scenario-based evaluations that verify personality alignment. If agent behavior degrades after personality changes, changes are blocked until alignment is restored. Agent personalities are versioned alongside code to enable rollback.

**System level evals as preconditions for enabling new automation levels:** Moving from advisory to supervised to auto-execution with HITL requires system-level evaluation that demonstrates safety, SLA adherence, and planner trust. For example, enabling autonomous conflict resolution (reducing HITL frequency) requires evidence that orchestrator resolves 90%+ of conflicts correctly without human intervention. Automation levels are gated by evaluation results, not by feature completion dates.

**Periodic re-evaluation and drift monitoring:** Even without code changes, agent behavior may drift due to: (1) LLM model updates (if agents use LLMs), (2) warehouse state distribution shifts (seasonality, operational changes), (3) tool output distribution shifts (if tools use machine learning). Periodic re-evaluation (weekly for agents, monthly for system) detects drift and triggers re-training or personality refinements if alignment degrades.

**Evaluation as continuous process, not one-time gate:** Evaluation is integrated into development workflow (pre-commit hooks for tool tests, CI/CD pipelines for agent tests, nightly system simulations) and production monitoring (real-time safety checks, SLA dashboards, HITL analytics). Evaluation is not a bottleneck but an enabler of safe, rapid iteration.

---

## 8. Next Steps

To operationalize this evaluation framework, engineering and product teams should prioritize the following work:

- **Select 2–3 high-impact tools and write full contracts using the template:** Start with tools that directly impact safety or SLA adherence (e.g., Capacity and Compatibility Checker, SLA Risk Estimator, Aisle Congestion Estimator). Write contracts using `tool_contracts/tool_contract_template.md`, implement unit tests with golden datasets, and establish baseline correctness metrics.

- **Define a minimal agent eval harness for 1–2 agents (e.g., SlottingAgent and PickingAgent):** Build test harness that can run agents with mocked tools, feed controlled warehouse contexts, and collect ProposedAction objects. Implement scenario-based tests that verify personality alignment (e.g., SlottingAgent defers when congestion high, PickingAgent escalates when SLA at risk). Establish baseline personality alignment scores.

- **Identify 2–3 realistic system scenarios for initial simulation-based evaluation:** Select scenarios that represent common warehouse operations (peak outbound, inbound surge, partial tool failure) and build end-to-end simulations that measure safety, SLA, and efficiency. Establish baseline system metrics (safety violation rate, order promise accuracy, autonomous conflict resolution rate).

- **Align with engineering and operations on which metrics matter most per level:** Work with warehouse operations teams to prioritize metrics (e.g., safety violations are zero-tolerance, order promise accuracy must meet 99.5% baseline, HITL frequency should not exceed 10 conflicts per hour). Establish SLAs for evaluation metrics (e.g., tool correctness must be 99%+, agent personality alignment must be 90%+, system safety violations must be 0%).

This framework is the backbone for safe deployment of agentic WMS features. It connects tool contracts (see `tool_contracts/tool_contract_template.md` and `tool_contracts/tool_catalog.md`), agent personalities (see `agent_design/agent_personalities.md`), orchestrator logic (see `prototype/orchestrator_logic.py`), and UX design (see `ux-flows/conflict_resolution_flow.md`) into a coherent evaluation story that enables incremental deployment: tools first (verified correctness), then agents (verified policy alignment), then system integration (verified safety and performance).

The framework should evolve as we learn from pilots and production usage. Initial evaluation criteria may be refined based on: (1) false positive rates (evaluations flagging safe behaviors as unsafe), (2) false negative rates (evaluations missing unsafe behaviors), (3) planner feedback on HITL frequency and quality, and (4) operational metrics that reveal gaps in evaluation coverage. However, this document defines the initial, explicit contract for how we judge success and safety, ensuring that agentic WMS features deploy with measurable quality and human trust.

---

**Document Status:** Ready for Engineering and Product Review  
**Next Steps:** Prioritize tool contracts, build agent eval harness, design system simulation scenarios, align on metrics SLAs

