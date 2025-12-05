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
4. Explains its reasoning

## Relationship to Repository

This demo aligns with the evaluation cases defined in `evals/picking_agent_cases.md`. The four scenarios in this demo correspond to the first four detailed evaluation cases:

1. **High SLA + Sufficient Labor + Low Congestion** - Tests SLA prioritization
2. **High SLA + Insufficient Labor** - Tests escalation behavior
3. **Low SLA + High Congestion** - Tests congestion awareness
4. **Conflicting/Partial Data** - Tests uncertainty handling

The demo is intentionally simplified for demonstration purposes and does not implement the full production logic described in the architecture documents.

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

## Using in an Interview

This demo can be used to demonstrate agent behavior in interviews:

1. **Select a scenario** - Choose one of the four predefined scenarios
2. **Run the agent** - Click "Run Agent" to see the decision
3. **Explain the decision** - Walk through:
   - Why the agent chose this action type
   - How risk scores were calculated
   - Why escalation was or wasn't triggered
4. **Review orchestrator reaction** - Show how the orchestrator responds to the agent's proposal
5. **Check evaluation** - Verify the agent's behavior matches expectations

The demo provides a concrete, interactive way to discuss:
- Agent decision-making logic
- Risk assessment and uncertainty handling
- Escalation criteria
- Evaluation frameworks
- Multi-agent coordination (orchestrator interaction)

