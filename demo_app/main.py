"""Streamlit UI for PickingAgent demo."""
from typing import Optional
import json
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
    
    # Convert action to dict for JSON export
    agent_output = {
        "action_type": action.action_type,
        "prioritised_orders": action.prioritised_orders,
        "deferred_orders": action.deferred_orders,
        "risk_score": action.risk_score,
        "uncertainty": action.uncertainty,
        "escalate": action.escalate,
        "explanation": action.explanation,
        "reasoning_summary": action.reasoning_summary
    }
    
    # Display agent decision
    st.header("🤖 Agent Decision")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Action Type", action.action_type.replace("_", " ").title())
        st.metric("Risk Score", f"{action.risk_score:.2f}")
    with col2:
        st.metric("Uncertainty", f"{action.uncertainty:.2f}")
        st.metric("Escalate", "Yes" if action.escalate else "No")
    
    # Agent reasoning summary (safe surrogate)
    with st.expander("🧠 Agent Reasoning (summarized)", expanded=False):
        st.write(
            agent_output.get(
                "reasoning_summary",
                "No reasoning summary is available for this run."
            )
        )
    
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
    
    # Convert orchestrator decision to dict for JSON export
    orch_output = {
        "auto_approve": orchestrator_decision.auto_approve,
        "hitl_required": orchestrator_decision.hitl_required,
        "comment": orchestrator_decision.comment
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Auto Approve", "Yes" if orchestrator_decision.auto_approve else "No")
    with col2:
        st.metric("HITL Required", "Yes" if orchestrator_decision.hitl_required else "No")
    
    st.subheader("Orchestrator Comment")
    st.info(orchestrator_decision.comment)
    
    # Evaluation
    eval_result = evaluate_decision(selected_scenario, action)
    
    # Evaluation header with status-based styling
    if eval_result.status == "PASS":
        st.header("✅ Evaluation")
        st.success("PASS")
    else:
        st.header("⚠️ Evaluation")
        st.error("FAIL")
    
    st.subheader("Evaluation Details")
    for check in eval_result.details:
        if check.get("pass", True):
            st.markdown(f"🟢 **PASS:** {check['description']}")
        else:
            st.markdown(f"🔴 **FAIL:** {check['description']}")
    
    # Expected vs Actual comparison
    st.subheader("Expected vs Actual")
    if eval_result.expected and eval_result.actual:
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            st.markdown("**Expected:**")
            if "action_type" in eval_result.expected:
                expected_action = eval_result.expected["action_type"]
                if expected_action != "varies":
                    st.metric("Action", expected_action.replace("_", " ").title())
            if "escalate" in eval_result.expected:
                expected_escalate = eval_result.expected["escalate"]
                if expected_escalate != "varies":
                    st.metric("Escalation / HITL Required", "Yes" if expected_escalate else "No")
            if "uncertainty_min" in eval_result.expected:
                uncertainty_min = eval_result.expected["uncertainty_min"]
                if uncertainty_min > 0:
                    st.metric("Uncertainty (min)", f"> {uncertainty_min:.2f}")
            if "risk_range" in eval_result.expected:
                risk_range = eval_result.expected["risk_range"]
                if risk_range != "varies":
                    st.metric("Risk Range", str(risk_range))
        
        with comp_col2:
            st.markdown("**Actual:**")
            st.metric("Action", eval_result.actual["action_type"].replace("_", " ").title())
            st.metric("Escalation / HITL Required", "Yes" if eval_result.actual["escalate"] else "No")
            st.metric("Uncertainty", f"{eval_result.actual['uncertainty']:.2f}")
            st.metric("Risk Score", f"{eval_result.actual['risk_score']:.2f}")
    
    # Download JSON log
    st.header("📥 Download Run JSON")
    scenario_dict = {
        "id": selected_scenario.id,
        "name": selected_scenario.name,
        "description": selected_scenario.description,
        "sla_pressure": selected_scenario.sla_pressure,
        "labor_capacity": selected_scenario.labor_capacity,
        "congestion": selected_scenario.congestion,
        "inventory_confidence": selected_scenario.inventory_confidence
    }
    
    eval_result_dict = {
        "status": eval_result.status,
        "passed": eval_result.passed,
        "details": eval_result.details,
        "expected": eval_result.expected,
        "actual": eval_result.actual,
        "messages": eval_result.messages
    }
    
    run_log = {
        "scenario_id": selected_scenario.id,
        "scenario": scenario_dict,
        "agent_output": agent_output,
        "orchestrator_output": orch_output,
        "evaluation": eval_result_dict,
    }
    
    json_bytes = json.dumps(run_log, indent=2).encode("utf-8")
    st.download_button(
        label="Download JSON log",
        data=json_bytes,
        file_name=f"picking_agent_run_{selected_scenario.id}.json",
        mime="application/json",
    )

