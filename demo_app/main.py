"""Streamlit UI for PickingAgent demo."""
from typing import Optional
import streamlit as st
from scenarios import Scenario, SCENARIOS, get_scenario_by_id
from picking_agent import PickingAgent
from orchestrator_stub import orchestrate, OrchestratorDecision
from evaluation import evaluate_decision, EvaluationResult
from semantics import describe_semantic_context

# Page config
st.set_page_config(
    page_title="PickingAgent Demo",
    page_icon="📦",
    layout="wide"
)

# Title
st.title("PickingAgent Demo – Agentic WMS Sandbox")

# Sidebar
st.sidebar.header("Scenario Selection")

# Scenario dropdown
scenario_names = [s.name for s in SCENARIOS]
selected_name = st.sidebar.selectbox(
    "Select a scenario:",
    options=scenario_names,
    index=0
)

# Get selected scenario
selected_scenario: Optional[Scenario] = None
for s in SCENARIOS:
    if s.name == selected_name:
        selected_scenario = s
        break

# Show scenario description in sidebar
if selected_scenario:
    st.sidebar.subheader("Scenario Description")
    st.sidebar.write(selected_scenario.description)

# Run button
run_agent = st.sidebar.button("Run Agent", type="primary")

# Main area
if not run_agent:
    st.info(
        "👆 Select a scenario from the sidebar and click 'Run Agent' to see "
        "how the PickingAgent makes decisions based on warehouse conditions."
    )
    st.markdown("### Instructions")
    st.markdown("""
    1. **Select a scenario** from the dropdown in the sidebar
    2. **Review the scenario description** to understand the warehouse context
    3. **Click "Run Agent"** to see the agent's decision
    4. **Review the results**:
       - Agent's proposed action and reasoning
       - Orchestrator's response
       - Evaluation results against expected behavior
    """)
else:
    if selected_scenario is None:
        st.error("No scenario selected.")
        st.stop()
    
    # Display scenario details
    with st.expander("📋 Scenario Details", expanded=True):
        st.subheader(selected_scenario.name)
        st.write(selected_scenario.description)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("SLA Pressure", selected_scenario.sla_pressure.upper())
        with col2:
            st.metric("Labor Capacity", selected_scenario.labor_capacity.upper())
        with col3:
            st.metric("Congestion", selected_scenario.congestion.upper())
        with col4:
            st.metric("Inventory Confidence", selected_scenario.inventory_confidence.upper())
        
        st.markdown("**Semantic Context:**")
        st.write(describe_semantic_context(selected_scenario))
    
    # Run agent
    agent = PickingAgent()
    action = agent.decide(selected_scenario)
    
    # Display agent decision
    st.header("🤖 Agent Decision")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Action Type", action.action_type.replace("_", " ").title())
        st.metric("Risk Score", f"{action.risk_score:.2f}")
    with col2:
        st.metric("Uncertainty", f"{action.uncertainty:.2f}")
        st.metric("Escalate", "Yes" if action.escalate else "No")
    
    st.subheader("Prioritised Orders")
    if action.prioritised_orders:
        for order in action.prioritised_orders:
            st.write(f"- {order}")
    else:
        st.write("None")
    
    st.subheader("Deferred Orders")
    if action.deferred_orders:
        for order in action.deferred_orders:
            st.write(f"- {order}")
    else:
        st.write("None")
    
    st.subheader("Explanation")
    st.text_area("", value=action.explanation, height=150, disabled=True, label_visibility="collapsed")
    
    # Orchestrator view
    st.header("🎯 Orchestrator View")
    orchestrator_decision = orchestrate(action)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Auto Approve", "Yes" if orchestrator_decision.auto_approve else "No")
    with col2:
        st.metric("HITL Required", "Yes" if orchestrator_decision.hitl_required else "No")
    
    st.subheader("Orchestrator Comment")
    st.info(orchestrator_decision.comment)
    
    # Evaluation
    st.header("✅ Evaluation")
    eval_result = evaluate_decision(selected_scenario, action)
    
    if eval_result.passed:
        st.success("PASS")
    else:
        st.error("FAIL")
    
    st.subheader("Evaluation Details")
    for message in eval_result.messages:
        st.write(message)

