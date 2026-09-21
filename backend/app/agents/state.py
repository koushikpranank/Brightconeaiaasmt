"""The shared state threaded through the LangGraph pipeline.

One `CaseState` dict per disruption case, accumulating each agent's output. This is what
makes the final report and the Reviewer Agent's job possible: every claim in the report
traces back to a specific field a specific agent populated, with the evidence that
justified it (see `audit_log`).
"""
from typing import Any, TypedDict


class CaseState(TypedDict, total=False):
    case_number: str
    event_id: int
    material: str
    disruption_type: str
    source: str
    description: str
    original_delivery_date: str | None
    revised_delivery_date: str | None

    inventory_analysis: dict[str, Any]
    impact: dict[str, Any]
    supplier_options: list[dict[str, Any]]
    mitigation: dict[str, Any]
    alert: dict[str, Any]
    review: dict[str, Any]

    revision_count: int
    status: str
    audit_log: list[dict[str, Any]]

    # Scratch fields threaded between nodes within one pipeline run (not persisted as
    # their own DB columns). Must be declared here - LangGraph only tracks state updates
    # for keys present in this schema and silently drops anything else.
    _observations: dict[str, Any]
    _confirmed: bool
    _delay_days: int
    _supplier_code: str
    _region_lat: float
    _region_lon: float


def log_step(state: CaseState, agent_name: str, input_summary: str, output_summary: str, evidence: dict | None = None) -> dict:
    entry = {
        "agent": agent_name,
        "input": input_summary,
        "output": output_summary,
        "evidence": evidence or {},
    }
    audit_log = list(state.get("audit_log", []))
    audit_log.append(entry)
    return {"audit_log": audit_log}
