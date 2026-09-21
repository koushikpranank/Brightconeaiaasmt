"""Orchestrates a full monitoring sweep: turns raw candidate signals into disruption
cases and drives each one through the seven-agent LangGraph pipeline.

Deduplication happens at the case level: if a case for the same (material,
disruption_type) is already open (not resolved/approved/rejected), a fresh monitoring
pass re-runs the pipeline against the *existing* case instead of spawning a new one, and
the Alert Agent's dedup_key prevents a duplicate alert from being raised for it. Only once
a case resolves (e.g. delivery restored, TC-05) does the next monitoring pass open a new
one for a later disruption on that material.
"""
from datetime import datetime

from sqlmodel import Session, select

from app.agents import monitoring_agent
from app.agents.graph import run_case
from app.agents.state import CaseState
from app.models import DisruptionCase, DisruptionEventRecord, PurchaseOrder, Supplier

OPEN_STATUSES = {"in_progress", "needs_revision", "pending_approval"}

KIND_TO_DISRUPTION_TYPE = {
    "supplier_delay": "supplier_delay",
    "shipment_delay": "shipment_delay",
    "low_inventory": "shortage",
    "supplier_unavailable": "supplier_unavailable",
    "lead_time_increase": "lead_time_increase",
}
DISRUPTION_TYPE_TO_KIND = {v: k for k, v in KIND_TO_DISRUPTION_TYPE.items()}

DECIDED_STATUSES = {"approved", "rejected"}
ACTIVE_STATUSES = OPEN_STATUSES | DECIDED_STATUSES  # everything except "resolved"


def _find_active_case(session: Session, material: str, disruption_type: str) -> DisruptionCase | None:
    """Most recent non-resolved case for this (material, disruption_type), if any."""
    events = session.exec(
        select(DisruptionEventRecord).where(
            DisruptionEventRecord.material == material, DisruptionEventRecord.disruption_type == disruption_type
        )
    ).all()
    event_ids = [e.id for e in events]
    if not event_ids:
        return None
    cases = session.exec(
        select(DisruptionCase).where(DisruptionCase.event_id.in_(event_ids)).order_by(DisruptionCase.updated_at.desc())
    ).all()
    for case in cases:
        if case.status in ACTIVE_STATUSES:
            return case
    return None


def _build_initial_state(event: DisruptionEventRecord, case_number: str, supplier_code: str | None, region: tuple | None) -> CaseState:
    state: CaseState = {
        "case_number": case_number,
        "event_id": event.id,
        "material": event.material,
        "disruption_type": event.disruption_type,
        "source": event.source,
        "description": event.description,
        "original_delivery_date": event.original_delivery_date.isoformat() if event.original_delivery_date else None,
        "revised_delivery_date": event.revised_delivery_date.isoformat() if event.revised_delivery_date else None,
        "revision_count": 0,
        "audit_log": [],
    }
    if supplier_code:
        state["_supplier_code"] = supplier_code
    if region:
        state["_region_lat"], state["_region_lon"] = region
    return state


def process_candidate(session: Session, candidate: dict) -> DisruptionCase | None:
    kind = candidate["kind"]
    disruption_type = KIND_TO_DISRUPTION_TYPE[kind]
    material = candidate.get("material")
    po_number = candidate.get("po_number")
    supplier_code = candidate.get("supplier_code")

    original_date = revised_date = None
    if po_number:
        po = session.exec(select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)).first()
        if po:
            material = material or po.material
            supplier_code = supplier_code or po.supplier_code
            original_date = po.original_delivery_date
            revised_date = po.revised_delivery_date

    if not material:
        return None

    existing_active_case = _find_active_case(session, material, disruption_type)
    if existing_active_case and existing_active_case.status in DECIDED_STATUSES:
        # A human already approved/rejected a mitigation plan for this disruption and
        # nothing about the underlying signal has changed enough to warrant a new case
        # (a genuinely new/worse signal - e.g. a second, larger delay - would arrive via a
        # fresh disruption_type or be surfaced by the reviewer on the next real change).
        return existing_active_case

    if po_number:
        source = f"po:{po_number}"
        description = f"{kind.replace('_', ' ').title()} detected for {material} via PO {po_number}."
    elif supplier_code:
        source = f"supplier:{supplier_code}"
        description = f"{kind.replace('_', ' ').title()} detected for supplier {supplier_code} ({material})."
    else:
        source = f"material:{material}"
        description = f"{kind.replace('_', ' ').title()} detected for {material}."

    event = DisruptionEventRecord(
        external_ref=po_number or supplier_code or material,
        material=material,
        disruption_type=disruption_type,
        source=source,
        description=description,
        original_delivery_date=original_date,
        revised_delivery_date=revised_date,
        raw_payload=candidate,
    )
    session.add(event)
    session.commit()
    session.refresh(event)

    region = None
    if supplier_code:
        supplier = session.exec(select(Supplier).where(Supplier.supplier_code == supplier_code)).first()
        if supplier and supplier.region_lat is not None and supplier.region_lon is not None:
            region = (supplier.region_lat, supplier.region_lon)

    if existing_active_case:
        case = existing_active_case
        case.event_id = event.id
        case.status = "in_progress"
        session.add(case)
        session.commit()
        session.refresh(case)
    else:
        case_number = f"CASE-{datetime.utcnow():%Y%m%d%H%M%S}-{event.id}"
        case = DisruptionCase(case_number=case_number, event_id=event.id, status="in_progress")
        session.add(case)
        session.commit()
        session.refresh(case)

    initial_state = _build_initial_state(event, case.case_number, supplier_code, region)
    run_case(session, case.id, initial_state)

    session.refresh(case)
    return case


def _gather_recheck_candidates(session: Session) -> list[dict]:
    """Re-examines every currently open case so a restored delivery/supplier is detected
    and the case is moved to resolved (TC-05), not left open forever once the underlying
    source signal disappears from scan_for_changes."""
    open_cases = session.exec(select(DisruptionCase).where(DisruptionCase.status.in_(OPEN_STATUSES))).all()
    candidates = []
    for case in open_cases:
        event = session.get(DisruptionEventRecord, case.event_id)
        if not event:
            continue
        kind = DISRUPTION_TYPE_TO_KIND.get(event.disruption_type)
        if not kind:
            continue
        po_number = event.source.split(":", 1)[1] if event.source.startswith("po:") else None
        supplier_code = event.source.split(":", 1)[1] if event.source.startswith("supplier:") else None
        candidates.append({"kind": kind, "po_number": po_number, "material": event.material, "supplier_code": supplier_code})
    return candidates


def run_monitoring_sweep(session: Session) -> list[DisruptionCase]:
    cases = []
    handled_keys: set[tuple] = set()

    for candidate in _gather_recheck_candidates(session):
        case = process_candidate(session, candidate)
        if case:
            cases.append(case)
            handled_keys.add((candidate.get("material"), KIND_TO_DISRUPTION_TYPE[candidate["kind"]]))

    for candidate in monitoring_agent.scan_for_changes(session):
        material = candidate.get("material")
        disruption_type = KIND_TO_DISRUPTION_TYPE[candidate["kind"]]
        if (material, disruption_type) in handled_keys:
            continue
        case = process_candidate(session, candidate)
        if case:
            cases.append(case)

    return cases
