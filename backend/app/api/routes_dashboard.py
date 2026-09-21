from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import ActionItem, Alert, ApprovalRequest, DisruptionCase, InventoryItem, Supplier

router = APIRouter(tags=["dashboard"])

OPEN_STATUSES = {"in_progress", "needs_revision", "pending_approval"}


@router.get("/dashboard/summary")
def dashboard_summary(session: Session = Depends(get_session)):
    cases = session.exec(select(DisruptionCase)).all()
    active_cases = [c for c in cases if c.status in OPEN_STATUSES]

    alerts = session.exec(select(Alert).where(Alert.status != "resolved")).all()
    suppliers = session.exec(select(Supplier)).all()
    at_risk_suppliers = [s for s in suppliers if s.status != "active"]

    inventory = session.exec(select(InventoryItem)).all()
    at_risk_materials = []
    for item in inventory:
        if item.daily_consumption > 0:
            coverage = item.current_quantity / item.daily_consumption
            if coverage <= item.reorder_point_days:
                at_risk_materials.append({"material": item.material, "coverage_days": round(coverage, 2)})

    pending_approvals = session.exec(select(ApprovalRequest).where(ApprovalRequest.status == "pending")).all()
    open_actions = session.exec(select(ActionItem).where(ActionItem.status != "done")).all()

    severity_counts: dict[str, int] = {}
    for c in active_cases:
        sev = (c.impact or {}).get("severity", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "active_disruptions": len(active_cases),
        "delayed_shipments": len([a for a in alerts if a.disruption_type == "shipment_delay"]),
        "at_risk_materials": at_risk_materials,
        "at_risk_suppliers": [s.supplier_code for s in at_risk_suppliers],
        "open_alerts": len(alerts),
        "pending_approvals": len(pending_approvals),
        "open_action_items": len(open_actions),
        "severity_breakdown": severity_counts,
    }
