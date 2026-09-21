"""Agent 7 (optional but implemented) - Reviewer / Critic Agent.

Independently re-runs the deterministic inventory calculation and diffs it against what
the Inventory Agent reported, checks that every conclusion downstream cites evidence
rather than asserting a number out of nowhere, and can send the case back to an earlier
node for revision (capped to avoid infinite loops).
"""
from datetime import datetime

from sqlmodel import Session

from app.agents.state import CaseState, log_step
from app.tools.inventory_math import calculate_inventory_coverage

MAX_REVISIONS = 2


def node(state: CaseState, session: Session) -> dict:
    issues: list[str] = []
    revision_target = None

    inventory_analysis = state.get("inventory_analysis", {})
    observations = state.get("_observations", {})
    snapshot = observations.get("inventory_snapshot")

    if snapshot:
        snapshot_at = datetime.fromisoformat(snapshot["snapshot_at"]) if snapshot["snapshot_at"] else None
        recheck = calculate_inventory_coverage(
            current_quantity=snapshot["current_quantity"],
            daily_consumption=snapshot["daily_consumption"],
            snapshot_at=snapshot_at,
            reorder_point_days=snapshot["reorder_point_days"],
        )
        if recheck.coverage_days != inventory_analysis.get("coverage_days"):
            issues.append(
                f"Recomputed coverage_days={recheck.coverage_days} does not match reported "
                f"{inventory_analysis.get('coverage_days')}."
            )
            revision_target = revision_target or "inventory"

    impact = state.get("impact", {})
    if impact.get("severity") in (None, "unknown") and inventory_analysis.get("stockout_calculable"):
        issues.append("Impact severity is 'unknown' despite a calculable stockout date - re-run impact assessment.")
        revision_target = revision_target or "impact_assessment"

    mitigation = state.get("mitigation", {})
    if not mitigation.get("options") and not mitigation.get("recommended_actions"):
        issues.append("No mitigation options or recommended actions were produced.")
        revision_target = revision_target or "mitigation_planning"

    for option in mitigation.get("options", []):
        if option.get("data_confidence") not in ("confirmed", "requires_verification"):
            issues.append(f"Supplier option {option.get('supplier_code')} is missing a data-confidence label.")
            revision_target = revision_target or "mitigation_planning"

    alert = state.get("alert", {})
    if not alert.get("dedup_key"):
        issues.append("Alert is missing a dedup key; duplicate alerts cannot be prevented.")
        revision_target = revision_target or "alert_response"

    revision_count = state.get("revision_count", 0)
    approved = len(issues) == 0 or revision_count >= MAX_REVISIONS

    if approved and issues:
        issues.append(f"Revision cap ({MAX_REVISIONS}) reached; escalating to human approval with open issues noted.")

    review = {
        "approved": approved,
        "issues": issues,
        "revision_target": None if approved else revision_target,
    }

    updates = {
        "review": review,
        "status": "pending_approval" if approved else "needs_revision",
        "revision_count": revision_count if approved else revision_count + 1,
    }
    updates.update(
        log_step(
            state,
            "Reviewer / Critic Agent",
            input_summary="Independently re-verifying calculations and evidence completeness",
            output_summary=f"approved={approved}; issues={len(issues)}",
            evidence=review,
        )
    )
    return updates
