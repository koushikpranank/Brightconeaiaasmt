"""LangGraph wiring for the seven-agent pipeline.

Monitoring -> Detection -> (confirmed?) -> Inventory -> Impact -> Mitigation -> Alert ->
Reviewer -> (approved?) -> END (case then waits at status="pending_approval" for a human
decision via the /approvals API) or looped back to the node the Reviewer flagged, capped
at reviewer_agent.MAX_REVISIONS retries.

Human approval is deliberately NOT modeled as a LangGraph interrupt/checkpoint: the graph
finishes each automated pass and persists the case to Postgres, and a plain REST endpoint
resumes the workflow afterward. This keeps the demo deployable without a checkpointer
backend while still giving the "requires human approval before commitment" behavior the
spec asks for.
"""
from datetime import datetime

from langgraph.graph import END, StateGraph
from sqlmodel import Session, select

from app.agents import alert_agent, detection_agent, impact_agent, inventory_agent, mitigation_agent, monitoring_agent, reviewer_agent
from app.agents.state import CaseState
from app.models import AgentDecisionLog, ApprovalRequest, DisruptionCase


def _route_after_detection(state: CaseState) -> str:
    return "continue" if state.get("_confirmed") else "resolved"


def _route_after_review(state: CaseState) -> str:
    review = state.get("review", {})
    if review.get("approved"):
        return "done"
    return review.get("revision_target") or "done"


def build_graph(session: Session, case_db_id: int):
    graph = StateGraph(CaseState)

    # Node names must not collide with CaseState keys (e.g. "impact", "mitigation", "alert"
    # are state fields) - LangGraph reserves state keys as channel names.
    graph.add_node("monitoring", lambda s: monitoring_agent.node(s, session))
    graph.add_node("detection", lambda s: detection_agent.node(s, session))
    graph.add_node("inventory", lambda s: inventory_agent.node(s, session))
    graph.add_node("impact_assessment", lambda s: impact_agent.node(s, session))
    graph.add_node("mitigation_planning", lambda s: mitigation_agent.node(s, session))
    graph.add_node("alert_response", lambda s: alert_agent.node(s, session, case_db_id))
    graph.add_node("reviewer", lambda s: reviewer_agent.node(s, session))

    graph.set_entry_point("monitoring")
    graph.add_edge("monitoring", "detection")
    graph.add_conditional_edges("detection", _route_after_detection, {"continue": "inventory", "resolved": END})
    graph.add_edge("inventory", "impact_assessment")
    graph.add_edge("impact_assessment", "mitigation_planning")
    graph.add_edge("mitigation_planning", "alert_response")
    graph.add_edge("alert_response", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        _route_after_review,
        {
            "done": END,
            "inventory": "inventory",
            "impact_assessment": "impact_assessment",
            "mitigation_planning": "mitigation_planning",
            "alert_response": "alert_response",
        },
    )

    return graph.compile()


def _persist_step(session: Session, case_db_id: int, node_name: str, state: CaseState) -> None:
    audit_log = state.get("audit_log", [])
    if audit_log:
        last = audit_log[-1]
        session.add(
            AgentDecisionLog(
                case_id=case_db_id,
                agent_name=last["agent"],
                input_summary=last["input"],
                output_summary=last["output"],
                evidence=last["evidence"],
            )
        )

    case_row = session.get(DisruptionCase, case_db_id)
    if case_row:
        previous_status = case_row.status
        case_row.status = state.get("status", case_row.status)
        case_row.inventory_analysis = state.get("inventory_analysis", case_row.inventory_analysis)
        case_row.impact = state.get("impact", case_row.impact)
        case_row.supplier_options = state.get("supplier_options", case_row.supplier_options)
        case_row.mitigation = state.get("mitigation", case_row.mitigation)
        case_row.review = state.get("review", case_row.review)
        case_row.revision_count = state.get("revision_count", case_row.revision_count)
        case_row.updated_at = datetime.utcnow()
        session.add(case_row)
        session.commit()

        if previous_status != "pending_approval" and case_row.status == "pending_approval":
            _create_approval_request(session, case_row, state)
        return

    session.commit()


def _create_approval_request(session: Session, case_row: DisruptionCase, state: CaseState) -> None:
    existing = session.exec(
        select(ApprovalRequest).where(ApprovalRequest.case_id == case_row.id, ApprovalRequest.status == "pending")
    ).first()
    if existing:
        return

    mitigation = state.get("mitigation", {})
    options = mitigation.get("options", [])
    best = options[0] if options and options[0].get("data_confidence") == "confirmed" else None
    estimated_cost = None
    required_quantity = mitigation.get("required_quantity")
    if best and best.get("price_per_unit") is not None and required_quantity is not None:
        estimated_cost = round(best["price_per_unit"] * required_quantity, 2)

    material = state.get("material")
    disruption_type = state.get("disruption_type")
    action_type, description = _determine_action_type(disruption_type, material, best, estimated_cost, mitigation)

    session.add(
        ApprovalRequest(
            case_id=case_row.id,
            action_type=action_type,
            description=description,
            estimated_cost=estimated_cost,
            status="pending",
        )
    )
    session.commit()


def _determine_action_type(
    disruption_type: str, material: str, best_confirmed_option: dict | None, estimated_cost: float | None, mitigation: dict
) -> tuple[str, str]:
    """Requirement 9 lists four distinct approval categories rather than one generic
    "review this" gate. Every case is mapped to exactly one, based on what the mitigation
    plan actually recommends - never guessed independently of the evidence already gathered.
    """
    if disruption_type == "shortage" and best_confirmed_option:
        return (
            "place_purchase_order",
            f"Approve placing a purchase order with {best_confirmed_option['name']} "
            f"({best_confirmed_option['supplier_code']}) to cover the {material} shortfall "
            f"(required quantity: {mitigation.get('required_quantity')}).",
        )

    if disruption_type in ("supplier_delay", "shipment_delay", "supplier_unavailable", "lead_time_increase") and best_confirmed_option:
        return (
            "change_supplier",
            f"Approve switching {material} sourcing to {best_confirmed_option['name']} "
            f"({best_confirmed_option['supplier_code']}, {best_confirmed_option['lead_time_days']}-day lead time) "
            f"in response to a {disruption_type.replace('_', ' ')}.",
        )

    if estimated_cost:
        return (
            "commit_expenditure",
            f"Approve additional spend (~{estimated_cost:,.2f}) to resolve the {material} disruption: "
            f"{mitigation.get('recommended_actions', ['-'])[0]}",
        )

    return (
        "modify_delivery_commitment",
        f"No confirmed alternative is available for {material} yet - approve revising the delivery "
        f"commitment for affected orders while sourcing is worked out: {mitigation.get('recommended_actions', ['-'])[0]}",
    )


def run_case(session: Session, case_db_id: int, initial_state: CaseState) -> CaseState:
    compiled = build_graph(session, case_db_id)
    final_state: dict = dict(initial_state)

    for step in compiled.stream(initial_state, stream_mode="updates"):
        for node_name, updates in step.items():
            final_state.update(updates)
            _persist_step(session, case_db_id, node_name, final_state)

    return final_state
