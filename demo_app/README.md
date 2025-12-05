# PickingAgent Demo

A simple Streamlit sandbox for demonstrating a PickingAgent in an agentic WMS (Warehouse Management System) context.

## What This Demo Is

This demo implements a single "hero" agent (PickingAgent) that makes decisions about order prioritization, wave planning, and escalation based on warehouse conditions. The agent evaluates scenarios with varying combinations of:

- Service level pressure (SLA deadlines)
- Labor capacity (worker availability)
- Congestion (aisle occupancy)
- Inventory confidence (data quality)

The demo shows how the agent:
1. Assesses risk using simple tool functions
2. Makes decisions about action types and order prioritization
3. Determines when to escalate to human planners
4. Explains its reasoning with a human-readable summary
5. Gets evaluated against expected behavior with structured pass/fail checks
6. Provides transparency through expected vs actual comparisons

## Relationship to Repository

This demo aligns with the evaluation cases defined in `evals/picking_agent_cases.md`. The four scenarios in this demo correspond to the first four detailed evaluation cases:

1. **High SLA + Sufficient Labor + Low Congestion** - Tests SLA prioritization (should PASS)
2. **High SLA + Insufficient Labor** - Tests escalation behavior (should PASS)
3. **Low SLA + High Congestion** - Tests congestion awareness (should PASS)
4. **Conflicting/Partial Data** - Tests uncertainty handling and safety (intentionally FAILS to demonstrate evaluation catching unsafe behavior)

**Note**: The `conflicting_partial_data` scenario is configured to intentionally fail evaluation. The agent makes an unsafe decision (proceeding with picking despite low inventory confidence) to demonstrate how the evaluation framework catches and flags unsafe behavior. This is useful for discussing safety mechanisms and evaluation rigor in production systems.

The demo is intentionally simplified for demonstration purposes and does not implement the full production logic described in the architecture documents.

## Key Features

### Agent Decision Making
- **Action Types**: Prioritize critical orders, defer low priority work, request inventory checks, or normal wave planning
- **Risk Assessment**: Calculates risk scores based on SLA pressure, labor capacity, congestion, and inventory confidence
- **Uncertainty Handling**: Tracks uncertainty when signals conflict or data quality is low
- **Escalation Logic**: Determines when to escalate to human-in-the-loop (HITL) for verification
- **Reasoning Summary**: Provides a human-readable summary of the agent's decision-making process (expandable in UI)

### Evaluation Framework
- **Structured Evaluation**: Each scenario has explicit expected behavior criteria
- **Visual Indicators**: Clear PASS (🟢) and FAIL (🔴) indicators for each evaluation check
- **Expected vs Actual Comparison**: Side-by-side comparison of expected vs actual agent behavior
- **Failure Demonstration**: One scenario (`conflicting_partial_data`) intentionally fails to demonstrate evaluation catching unsafe behavior

### Transparency & Logging
- **JSON Log Export**: Download complete run logs including scenario, agent output, orchestrator decision, and evaluation results
- **Detailed Evaluation Details**: Each check shows what was expected and what the agent actually did
- **Orchestrator Interaction**: Shows how the orchestrator responds to agent proposals (auto-approve vs HITL required)

## How to Run Locally

1. Install dependencies:
   ```bash
   pip install -r demo_app/requirements.txt
   ```

2. Run the Streamlit app:
   ```bash
   streamlit run demo_app/main.py
   ```

3. Open your browser to the URL shown in the terminal (typically `http://localhost:8501`)

OR

1. Click here for the prototype built using Replit - https://streamlit-wms-pickingagent-demo.replit.app

## Using in an Interview

This demo can be used to demonstrate agent behavior :

1. **Select a scenario** - Choose one of the four predefined scenarios
2. **Run the agent** - Click "Run Agent" to see the decision
3. **Review agent reasoning** - Expand the "🧠 Agent Reasoning (summarized)" section to see the agent's thought process
4. **Explain the decision** - Walk through:
   - Why the agent chose this action type
   - How risk scores were calculated
   - Why escalation was or wasn't triggered
5. **Review orchestrator reaction** - Show how the orchestrator responds to the agent's proposal
6. **Check evaluation** - Review the evaluation section:
   - See which checks passed (🟢) or failed (🔴)
   - Compare expected vs actual behavior
   - For the `conflicting_partial_data` scenario, demonstrate how evaluation catches unsafe behavior
7. **Export run log** - Download the JSON log to show complete traceability



