from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.integrations.supplier_api import announce_delay, announce_lead_time_increase, restore_lead_time
from app.models import ActionItem, ApprovalRequest, DisruptionCase, PurchaseOrder
from app.schemas import ActionItemUpdateIn, ApprovalDecisionIn, LeadTimeIncreaseEventIn, SupplierDelayEventIn
from app.services.case_runner import run_monitoring_sweep

router = APIRouter(tags=["workflow"])


@router.get("/actions")
def list_actions(session: Session = Depends(get_session)):
    return session.exec(select(ActionItem).order_by(ActionItem.created_at.desc())).all()


@router.patch("/actions/{action_id}")
def update_action(action_id: int, payload: ActionItemUpdateIn, session: Session = Depends(get_session)):
    action = session.get(ActionItem, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action item not found")
    action.status = payload.status
    action.updated_at = datetime.utcnow()
    session.add(action)
    session.commit()
    session.refresh(action)
    return action


@router.get("/approvals")
def list_approvals(session: Session = Depends(get_session)):
    return session.exec(select(ApprovalRequest).order_by(ApprovalRequest.requested_at.desc())).all()


@router.post("/approvals/{approval_id}/decision")
def decide_approval(approval_id: int, payload: ApprovalDecisionIn, session: Session = Depends(get_session)):
    """Requirement 9: no purchase order, supplier change, expenditure, or delivery-commitment
    change happens without a human decision recorded here."""
    approval = session.get(ApprovalRequest, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if payload.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")

    approval.status = payload.decision
    approval.decided_by = payload.approver
    approval.decided_at = datetime.utcnow()
    approval.notes = payload.notes
    session.add(approval)

    case = session.get(DisruptionCase, approval.case_id)
    if case:
        case.status = "approved" if payload.decision == "approved" else "rejected"
        case.updated_at = datetime.utcnow()
        session.add(case)

    session.commit()
    session.refresh(approval)
    return approval


@router.post("/monitoring/run")
def trigger_monitoring_sweep(session: Session = Depends(get_session)):
    cases = run_monitoring_sweep(session)
    return {"checked_at": datetime.utcnow().isoformat(), "cases_processed": [c.case_number for c in cases]}


@router.post("/monitoring/simulate-delay")
def simulate_supplier_delay(payload: SupplierDelayEventIn, session: Session = Depends(get_session)):
    """Demo/testing hook: simulates the supplier portal announcing a delivery delay,
    then immediately runs a monitoring sweep so the pipeline reacts to it (TC-01)."""
    result = announce_delay(session, payload.po_number, payload.delay_days, payload.reason)
    cases = run_monitoring_sweep(session)
    return {"delay_announced": result, "cases_processed": [c.case_number for c in cases]}


@router.post("/monitoring/simulate-restore/{po_number}")
def simulate_delivery_restored(po_number: str, session: Session = Depends(get_session)):
    """Demo/testing hook: simulates the supplier restoring the original delivery date,
    covering TC-05 (delivery schedule restored -> updated disruption status)."""
    po = session.exec(select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.revised_delivery_date = None
    po.status = "open"
    session.add(po)
    session.commit()

    cases = run_monitoring_sweep(session)
    return {"restored": po_number, "cases_processed": [c.case_number for c in cases]}


@router.post("/monitoring/simulate-lead-time-increase")
def simulate_lead_time_increase(payload: LeadTimeIncreaseEventIn, session: Session = Depends(get_session)):
    """Demo/testing hook: simulates a supplier quoting a longer lead time than what's on
    file, covering the sixth disruption type (unusual lead-time increase)."""
    result = announce_lead_time_increase(session, payload.supplier_code, payload.new_lead_time_days)
    cases = run_monitoring_sweep(session)
    return {"lead_time_updated": result, "cases_processed": [c.case_number for c in cases]}


@router.post("/monitoring/simulate-lead-time-restore/{supplier_code}")
def simulate_lead_time_restored(supplier_code: str, session: Session = Depends(get_session)):
    """Demo/testing hook: simulates the supplier's lead time returning to baseline."""
    try:
        result = restore_lead_time(session, supplier_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    cases = run_monitoring_sweep(session)
    return {"restored": result, "cases_processed": [c.case_number for c in cases]}
