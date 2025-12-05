# Tools vs. Agents: Design Foundation for Agentic WMS Evaluation

**Document Version:** 1.0  
**Author:** Senior Product Management  
**Date:** December 2025  
**Audience:** Engineering Leadership, Product Strategy, Quality Assurance

---

## 1. Why this distinction matters

In an agentic Warehouse Management System, the boundary between tools and agents determines how we design, test, and deploy capabilities. A fuzzy boundary leads to confused responsibilities, poor observability, and unclear evaluation criteria. When a slotting optimization engine is treated as an agent, we lose the ability to unit test its core algorithm. When a SlottingAgent is treated as a tool, we cannot evaluate its decision-making quality or personality alignment.

This document establishes a sharp distinction that enables three critical outcomes: (1) **tools that are testable and contract-driven**, with deterministic behavior that can be verified through unit tests and golden datasets, (2) **agents that are goal-directed decision makers**, with observable reasoning, personality alignment, and escalation behavior that can be evaluated through scenario-based tests, and (3) **evaluation frameworks that operate at tool, agent, and system levels**, allowing us to measure correctness, policy adherence, and end-to-end performance independently.

Without this separation, we cannot answer fundamental questions: Is the slotting algorithm correct? Does the SlottingAgent use it appropriately? Does the entire system maintain safety and SLA commitments? This document provides the conceptual foundation needed to answer these questions through structured evaluation.

---

## 2. Definition: What is a Tool in this architecture

A **tool** is a deterministic, stateless function that performs a specific computation or data transformation. It answers "given these inputs and constraints, what are the options and scores?" Tools have no goals, no memory beyond their immediate invocation, and no responsibility for explaining decisions to humans. They are invoked by agents or other services, never self-starting.

**Key characteristics:**

- **Narrow scope:** Does one thing or a closely related family of operations (e.g., scoring storage locations, calculating replenishment quantities, estimating travel times).

- **Deterministic and repeatable:** Same inputs lead to the same outputs, or randomness is controlled and logged. Given identical warehouse state and parameters, a tool produces identical results.

- **Invoked, never self-starting:** It does not wake up on its own. It is called by an agent or another service when computation is needed.

- **Bounded or stateless:** Any internal state is limited to the current invocation. Long-term state lives in data stores (semantic graph, databases). Tools do not maintain context across calls.

- **Contract-driven:** Clear input schema, output schema, preconditions, postconditions, and error codes. Tools validate inputs, return structured outputs, and fail fast on invalid data.

- **No goals of its own:** It does not decide what the overall objective is. It computes answers to questions posed by its caller.

- **Not responsible for narrative explanation to humans:** Although it may emit metadata (scores, confidence intervals, constraint violations) to support explanations, tools do not generate natural language rationale.

**WMS-specific examples:**

- **Storage location scoring tool (slotting engine):** Given a SKU, demand patterns, and physical constraints (weight, volume, hazard classes), returns ranked list of candidate storage locations with scores. The tool does not decide whether slotting should occur; it only answers "if we were to slot this SKU, which locations are best?"

- **Replenishment calculator:** Given a pick face location, current stock, reorder point, and reserve availability, returns recommended replenishment quantity and timing. The tool does not decide whether replenishment is warranted; it only answers "if we were to replenish, how much and when?"

- **Aisle congestion estimator:** Given aisle dimensions, current occupancy, scheduled operations, and movement patterns, returns congestion score and capacity warnings. The tool does not decide whether operations should be deferred; it only answers "what is the congestion risk for this aisle at this time?"

- **Dock scheduling solver:** Given trailer appointments, carrier cut-offs, door availability, and equipment status, returns optimal door assignments and timing. The tool does not decide whether a trailer should be accepted; it only answers "if we were to schedule this trailer, which door and when?"

These tools can exist even in a non-agentic WMS. They are deterministic algorithms that can be called by rule-based systems, human planners, or agents. The agentic layer adds decision-making on top of these tools.

---

## 3. Definition: What is an Agent in this architecture

An **agent** is a goal-directed decision maker that reasons about context, chooses and sequences tools, manages uncertainty, and explains its decisions. It answers "should we act at all now, which option should we choose, and how should we explain it?" Agents have explicit objectives, maintain context awareness, and align with defined personalities.

**Key characteristics:**

- **Goal-directed:** Optimizes for an explicit objective (e.g., "keep pick faces healthy while respecting constraints," "ensure orders are picked on-time," "prevent stockouts"). The agent decides what actions to take to achieve its goal.

- **Context-aware:** Can consider multiple signals, not just a single tool's inputs. An agent evaluates warehouse state, active operations, historical patterns, and competing priorities before making decisions.

- **Capable of choosing and sequencing tools:** Decides which tools to call, in what order, with what parameters. An agent may call multiple tools, compare results, and synthesize recommendations.

- **Manages uncertainty and escalation:** Decides when to act autonomously, when to defer to the Orchestrator, and when to escalate to a planner (HITL). Agents have confidence thresholds and escalation triggers defined in their personalities.

- **Responsible for explanation:** Packages tool outputs and context into a structured rationale for the Orchestrator and planner. Agents generate natural language explanations that include data sources, constraints evaluated, and tradeoffs considered.

- **Aligns with a defined personality:** Honors the objectives, risk posture, and communication style defined in `agent_design/agent_personalities.md`. Agents exhibit consistent behavior patterns that can be evaluated for personality alignment.

- **May be non-deterministic at the reasoning layer:** Even if tools are deterministic, the planning and tradeoffs can vary based on context, uncertainty, and personality-driven preferences. This is why evaluation is required.

**WMS-specific examples:**

- **SlottingAgent:** Decides whether any slotting action is warranted, then calls the slotting tool only for the right SKUs and locations. It evaluates congestion risk, timing tradeoffs, and operational impact before proposing movements. It may defer slotting during peak hours even if the tool recommends it, or escalate when conflicts exist with high-priority picking.

- **ReplenishmentAgent:** Decides when and where replenishment should occur, not only calculating quantities. It evaluates stockout risk, forklift availability, aisle safety, and picking schedules before proposing replenishment. It may batch multiple locations for efficiency, or escalate when stockout risk is high but conflicts with high-priority operations.

- **PickingAgent:** Decides when to reprioritize work to meet SLAs, and when to escalate a capacity issue instead of over-promising. It evaluates order priorities, worker availability, location status, and promise dates before proposing pick assignments. It may accept suboptimal pick paths to meet SLA commitments, or escalate when promise dates cannot be met.

The agent is not "the algorithm." The algorithm lives in tools. The agent decides when and how to use them, synthesizes results, manages tradeoffs, and explains decisions.

---

## 4. Tool catalog by micro-agent

This is a first-pass catalog of candidate tool families under each micro-agent. This is a starting point, not a complete inventory. Tools will be refined as agents are implemented and evaluated.

### 4.1 SlottingAgent – candidate tools

- **Storage location scoring tool (slotting engine):** Given SKU, demand patterns, and constraints, returns ranked locations with scores.

- **Travel time estimator:** Given pick frequency, location coordinates, and worker patterns, returns estimated travel time savings for location moves.

- **Aisle congestion estimator:** Given aisle dimensions, occupancy, and scheduled operations, returns congestion score and capacity warnings.

- **Capacity and compatibility checker:** Given item attributes (weight, volume, hazard classes, temperature) and location constraints, returns compatibility validation and capacity availability.

### 4.2 ReplenishmentAgent – candidate tools

- **Replenishment job generator:** Given location, stock level, reorder point, and reserve availability, returns recommended quantity and timing.

- **Safety stock calculator or threshold checker:** Given consumption patterns, lead times, and variability, returns reorder point and safety stock recommendations.

- **Task grouping and batching helper:** Given multiple replenishment needs in same aisle or zone, returns optimal batching strategy to minimize forklift trips.

- **Lift equipment availability checker:** Given forklift requirements and current assignments, returns availability status and estimated wait times.

### 4.3 PickingAgent – candidate tools

- **Wave or batch building tool:** Given orders, priorities, and cut-off times, returns optimal wave/batch groupings.

- **Route or pick path optimiser:** Given pick locations, worker starting position, and constraints, returns optimized pick sequence and path.

- **SLA risk estimator per order or wave:** Given promise dates, cut-off times, current time, and estimated pick/pack/ship durations, returns SLA risk scores and time buffers.

- **Picker workload balancer:** Given worker capacity, skills, and task assignments, returns workload distribution scores and balancing recommendations.

### 4.4 Dock/Yard Agent – candidate tools

- **Door assignment solver:** Given trailer appointments, carrier cut-offs, door availability, and equipment, returns optimal door assignments and timing.

- **Trailer dwell time estimator:** Given trailer arrival time, processing requirements, and current dock status, returns estimated dwell time and bottleneck warnings.

- **Appointment and schedule optimiser:** Given inbound/outbound trailers, appointments, and carrier requirements, returns optimized schedule that meets cut-offs and maximizes throughput.

### 4.5 Labor Sync Agent – candidate tools

- **Labor capacity forecaster:** Given worker schedules, skills, and historical performance, returns capacity forecasts by zone and time window.

- **Task to worker assignment optimiser:** Given tasks, worker skills, capacity, and proximity, returns optimal assignments that balance efficiency and fairness.

- **Shift and break compliance checker:** Given worker schedules, labor rules, and current assignments, returns compliance validation and break scheduling recommendations.

### 4.6 Inventory Accuracy Agent – candidate tools

- **Anomaly detector for inventory discrepancies:** Given system inventory, sensor data, and transaction history, returns discrepancy scores and anomaly flags.

- **Cycle count planner:** Given discrepancy patterns, location criticality, and operational schedules, returns prioritized cycle count recommendations and timing.

- **Confidence scoring tool for locations and SKUs:** Given transaction history, cycle count frequency, and discrepancy patterns, returns confidence scores for location and SKU accuracy.

Each tool is oriented to deterministic or rule-based behavior. Tools do not make decisions; they compute answers to specific questions.

---

## 5. Responsibility split: Agent versus Tool

The fundamental split is:

- **Tools answer:** "Given this question and these constraints, what are the options and scores?"

- **Agents answer:** "Should we act at all now, which option should we choose, and how should we explain it?"

**Concrete WMS scenarios where this distinction matters:**

**Scenario 1: Slotting tool returns an aggressive relocation plan in a busy aisle.**

- **Tool responsibility:** The slotting engine correctly calculates that moving Item X from Location A to Location B would reduce travel time by 40%. It returns ranked locations with scores.

- **Agent responsibility:** The SlottingAgent evaluates the tool's recommendation against current congestion, active picking operations, and timing constraints. It decides to defer the movement because congestion risk is high during peak hours, even though the tool recommends it. The agent explains: "Tool recommends movement with 40% travel time reduction, but aisle congestion is 0.75 (above 0.70 threshold) and 3 high-priority picks scheduled in next 30 minutes. Deferring to off-peak window."

**Scenario 2: Replen tool recommends many small jobs.**

- **Tool responsibility:** The replenishment calculator correctly identifies 8 locations below reorder point and recommends replenishment quantities for each. It returns individual job recommendations.

- **Agent responsibility:** The ReplenishmentAgent evaluates the tool's recommendations and decides to batch 5 locations in the same aisle into a single forklift trip for efficiency, while scheduling the remaining 3 locations for a later window. The agent explains: "Tool recommends 8 individual replenishment jobs. Batching 5 locations in Aisle A-12 into single trip (saves 20 minutes forklift time). Scheduling remaining 3 for 2:00 PM window to avoid peak picking."

**Scenario 3: Picking tool generates a route that technically meets SLA but overloads a single worker.**

- **Tool responsibility:** The pick path optimizer correctly calculates a route that meets the promise date with a 15-minute buffer. It returns an optimized sequence and estimated time.

- **Agent responsibility:** The PickingAgent evaluates the tool's route against worker capacity, fatigue constraints, and fair distribution policies. It decides to escalate to Labor Sync Agent instead of blindly accepting the route, because the route would overload Worker 123 beyond capacity limits. The agent explains: "Tool recommends route that meets SLA (15-minute buffer), but would assign 6 hours of work to Worker 123 who has 4 hours capacity remaining. Escalating to Labor Sync for reassignment to maintain fair distribution and prevent fatigue."

In each scenario, the tool provides correct computation, but the agent makes the decision about whether and how to act, considering context, constraints, and tradeoffs that the tool cannot evaluate.

---

## 6. Implications for evaluation

This separation enables three-level evaluation that measures correctness, policy alignment, and system performance independently.

### 6.1 Tool level evaluation

**What we test:** Correctness, performance, stability, data contract adherence.

**Methods:**
- **Unit tests:** Verify tool outputs for known inputs match expected results.
- **Golden datasets:** Test tools against historical warehouse scenarios with known correct answers.
- **Regression tests:** Ensure tool behavior remains consistent across code changes.
- **Performance benchmarks:** Measure tool latency and throughput under load.
- **Contract validation:** Verify tools reject invalid inputs and return structured outputs per schema.

**Examples:**
- Slotting engine unit test: Given SKU with 12 picks/day, forward pick location available, verify tool returns forward pick location as top-ranked option with score > 0.8.
- Replenishment calculator golden dataset: Given location with 15 units (reorder point: 20), daily consumption: 8 units/day, verify tool recommends replenishment quantity of 25 units.
- Congestion estimator regression test: Given same aisle state and operations, verify tool returns identical congestion score across versions.

**Success criteria:** Tools achieve 99%+ correctness on golden datasets, meet latency requirements (<100ms for most tools), and maintain backward compatibility on contract changes.

### 6.2 Agent level evaluation

**What we test:** Policy and personality alignment, correct tool usage, escalation behavior, explanation quality.

**Methods:**
- **Scenario-based evals:** Generate synthetic warehouse contexts and verify agents behave according to `agent_design/agent_personalities.md`.
- **Tool usage validation:** Verify agents call appropriate tools with correct parameters and interpret results correctly.
- **Escalation correctness:** Verify agents escalate when confidence thresholds or risk levels are exceeded.
- **Explanation quality:** Evaluate agent explanations for completeness, clarity, and evidence-based reasoning.
- **Personality alignment:** Measure consistency with defined risk postures, preferences, and communication styles.

**Examples:**
- SlottingAgent scenario: Given congestion score 0.75 and high-priority picking in aisle, verify agent defers slotting proposal (personality: low risk tolerance for congestion).
- ReplenishmentAgent escalation test: Given stockout risk < 2 hours but conflict with high-priority picking, verify agent escalates to Orchestrator (personality: escalates when stockout risk high but conflicts exist).
- PickingAgent explanation quality: Given order with tight SLA, verify agent explanation includes SLA status, time buffer, and alternative options considered.

**Success criteria:** Agents achieve 90%+ personality alignment on scenario tests, escalate correctly 95%+ of the time when thresholds exceeded, and generate explanations that human evaluators rate 85%+ as "clear and actionable."

### 6.3 System level evaluation

**What we test:** Safety, SLA performance, congestion, human trust.

**Methods:**
- **End-to-end simulations:** Run full warehouse operations with multiple agents, conflicts, and disruptions to measure system-wide performance.
- **Safety validation:** Verify no safety rule violations occur across all agent operations.
- **SLA compliance:** Measure order promise date accuracy, pick accuracy, and inventory accuracy across production-like scenarios.
- **Conflict resolution quality:** Evaluate Orchestrator's ability to resolve conflicts without human intervention while maintaining safety and SLA commitments.
- **Human trust metrics:** Measure planner approval rates, override frequency, and satisfaction with agent recommendations.

**Examples:**
- End-to-end simulation: Run 1000 orders through full pick-pack-ship cycle with concurrent slotting, replenishment, and picking operations. Measure SLA compliance, congestion levels, and safety violations.
- Safety validation: Verify no forklift-worker proximity violations, aisle capacity overruns, or equipment safety violations across all agent proposals.
- Conflict resolution test: Generate 100 conflict scenarios (slotting vs replenishment, picking vs labor) and verify Orchestrator resolves 90%+ without human intervention while maintaining safety and SLA.

**Success criteria:** System achieves 99%+ safety compliance, 99.5%+ order promise accuracy, 99.9%+ inventory accuracy, and 85%+ autonomous conflict resolution rate.

A separate agent evaluation framework document will formalize metrics, test harnesses, and sampling strategies. This note establishes the conceptual separation needed for that work.

---

## 7. Summary

**Tools are deterministic, narrow, and contract-driven.** They perform specific computations, answer specific questions, and can be tested through unit tests and golden datasets. Tools exist independently of agents and can be used by rule-based systems, human planners, or agents.

**Agents are goal-directed, context-aware, and personality-aligned.** They decide when and how to use tools, synthesize results, manage tradeoffs, and explain decisions. Agents require scenario-based evaluation to measure policy adherence, escalation correctness, and explanation quality.

**The Orchestrator sits above them** to resolve conflicts, protect global objectives, and coordinate agent proposals. The Orchestrator evaluates agent proposals, detects conflicts, applies arbitration rules, and routes to HITL when risk or uncertainty exceeds thresholds.

**This separation allows clean evaluation and safer deployment** of agentic WMS features. We can verify tool correctness independently of agent behavior, measure agent personality alignment independently of system performance, and evaluate system-wide safety and SLA compliance independently of individual component quality. This three-level evaluation framework enables incremental deployment: tools first (verified correctness), then agents (verified policy alignment), then system integration (verified safety and performance).

Without this separation, we cannot answer whether failures are due to incorrect algorithms, poor agent decisions, or system-level coordination issues. With this separation, we can diagnose, fix, and improve each layer independently, enabling faster iteration and safer production deployment.

---

**Document Status:** Ready for Engineering and Product Review  
**Next Steps:** Develop detailed tool specifications, implement tool-level unit tests, design agent-level scenario evaluation framework, and establish system-level simulation harnesses.

