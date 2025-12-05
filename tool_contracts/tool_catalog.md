# Tool Catalog for Agentic WMS

## 1. How to read this catalog

Each tool listed here should eventually have its own contract written using `tool_contracts/tool_contract_template.md`. The goal of this catalog is to show which deterministic capabilities exist or are needed under each micro agent. This is a structured inventory that engineering and PMs can refine later—it is not a full PRD for each tool, but rather a concise overview that identifies candidate tools and their primary purposes.

---

## 2. Tool families by micro agent

### 2.1 SlottingAgent – candidate tools

| Tool name | Purpose | Primary consumers | Notes |
|-----------|---------|-------------------|-------|
| Storage Location Scoring Tool | Rank candidate storage locations for a SKU based on velocity, compatibility, travel time, and constraints. | SlottingAgent | Must integrate with travel time data and compatibility rules. |
| Travel Time Estimator | Estimate travel time between locations for different equipment types. | SlottingAgent, PickingAgent | Shared capability used across multiple agents. |
| Aisle Congestion Estimator | Estimate congestion risk for aisle segments based on queued and in progress tasks. | SlottingAgent, ReplenishmentAgent, PickingAgent | Shared capability that enables proactive conflict avoidance. |
| Capacity and Compatibility Checker | Validate that a pallet or case is allowed in a location based on weight, volume, hazard class, and policy. | SlottingAgent | Critical safety and policy enforcement before slotting decisions. |

### 2.2 ReplenishmentAgent – candidate tools

| Tool name | Purpose | Primary consumers | Notes |
|-----------|---------|-------------------|-------|
| Replenishment Job Generator | Propose replenishment moves when pick faces fall below thresholds. | ReplenishmentAgent | Core capability that triggers replenishment proposals. |
| Safety Stock Threshold Checker | Evaluate whether current inventory is below configured safety levels. | ReplenishmentAgent, InventoryAccuracyAgent | Shared capability that supports stockout prevention. |
| Task Grouping Helper | Group individual replenishment moves into efficient batches. | ReplenishmentAgent | Optimizes forklift utilization and reduces aisle congestion. |
| Equipment Availability Checker | Check availability of forklifts or other required equipment for replenishment moves. | ReplenishmentAgent | Prevents proposals that cannot execute due to resource constraints. |

### 2.3 PickingAgent – candidate tools

| Tool name | Purpose | Primary consumers | Notes |
|-----------|---------|-------------------|-------|
| Wave or Batch Builder | Group orders or order lines into efficient pick waves or batches. | PickingAgent | Core capability that optimizes picking throughput. |
| Route or Pick Path Optimiser | Generate efficient pick paths through the warehouse layout. | PickingAgent | Must respect aisle constraints and congestion patterns. |
| SLA Risk Estimator | Estimate risk of SLA miss for orders or waves based on current state. | PickingAgent, Orchestrator | Shared capability that enables proactive SLA protection. |
| Picker Workload Balancer | Suggest distribution of work across available pickers. | PickingAgent, LaborSyncAgent | Shared capability that supports labor optimization. |

### 2.4 DockYardAgent – candidate tools

| Tool name | Purpose | Primary consumers | Notes |
|-----------|---------|-------------------|-------|
| Door Assignment Solver | Assign trailers to doors based on schedule, capacity, and constraints. | DockYardAgent | Core capability that optimizes dock utilization. |
| Trailer Dwell Time Estimator | Estimate expected dwell time per trailer given current workload. | DockYardAgent, Orchestrator | Shared capability that enables congestion forecasting. |
| Appointment Schedule Optimiser | Suggest adjustments to appointments to smooth peaks and avoid congestion. | DockYardAgent | Proactive capability that prevents scheduling conflicts. |

### 2.5 LaborSyncAgent – candidate tools

| Tool name | Purpose | Primary consumers | Notes |
|-----------|---------|-------------------|-------|
| Labor Capacity Forecaster | Forecast available labor capacity by skill and time window. | LaborSyncAgent, PickingAgent, ReplenishmentAgent | Shared capability that enables demand-capacity matching. |
| Task to Worker Assignment Tool | Propose assignments of tasks to workers respecting skills and rules. | LaborSyncAgent | Core capability that optimizes worker utilization. |
| Shift and Break Compliance Checker | Check that proposed schedules and assignments respect shift, break, and fatigue rules. | LaborSyncAgent | Critical compliance capability that prevents policy violations. |

### 2.6 InventoryAccuracyAgent – candidate tools

| Tool name | Purpose | Primary consumers | Notes |
|-----------|---------|-------------------|-------|
| Inventory Anomaly Detector | Detect potential mismatches between system and physical inventory. | InventoryAccuracyAgent | Core capability that identifies discrepancies. |
| Cycle Count Planner | Propose cycle count tasks based on risk, value, and recent activity. | InventoryAccuracyAgent | Optimizes cycle count efficiency and accuracy. |
| Location Confidence Scorer | Assign confidence scores to locations or SKUs based on error history and events. | InventoryAccuracyAgent, Orchestrator | Shared capability that enables risk-based decision making. |

---

## 3. Relationship to agents and orchestrator

Tools are shared capabilities. Multiple agents may call the same tool with different context—for example, the Travel Time Estimator is used by both SlottingAgent and PickingAgent, but each agent interprets the results according to their own objectives (optimization vs. execution planning).

Agents are responsible for deciding when and how to call tools, and for interpreting results according to their personality and objectives. The SlottingAgent might use location scoring to propose movements, while the Orchestrator might use the same scoring tool to validate proposals against global constraints.

The Orchestrator may call some tools directly for global reasoning, such as congestion or SLA risk estimators. These tools provide system-wide visibility that enables conflict detection and resolution beyond what individual agents can assess.

---

## 4. Next steps

Priority tools to specify first based on risk and impact:

- **High priority:** Tools that directly impact safety, SLA adherence, or conflict resolution (e.g., Capacity and Compatibility Checker, SLA Risk Estimator, Safety Stock Threshold Checker, Location Confidence Scorer)
- **Medium priority:** Core operational tools that enable agent proposals (e.g., Storage Location Scoring Tool, Replenishment Job Generator, Wave or Batch Builder, Door Assignment Solver)
- **Lower priority:** Optimization and efficiency tools that can be refined iteratively (e.g., Task Grouping Helper, Route or Pick Path Optimiser, Appointment Schedule Optimiser)

Future work will:

- Fill out individual tool contracts using the shared template in `tool_contracts/tool_contract_template.md`, starting with high-priority tools
- Connect tool level tests to the three level evaluation framework for tools, agents, and system behaviour
- Refine tool specifications based on agent personality requirements and orchestrator coordination needs
- Establish tool versioning and backward compatibility policies as tools evolve

