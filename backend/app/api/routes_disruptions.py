from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Alert, AgentDecisionLog, DisruptionCase, DisruptionEventRecord

router = APIRouter(tags=["disruptions"])


def _case_to_dict(session: Session, case: DisruptionCase) -> dict:
    event = session.get(DisruptionEventRecord, case.event_id)
    return {
        "id": case.id,
        "case_number": case.case_number,
        "status": case.status,
        "material": event.material if event else None,
        "disruption_type": event.disruption_type if event else None,
        "source": event.source if event else None,
        "description": event.description if event else None,
        "detected_at": event.detected_at.isoformat() if event else None,
        "original_delivery_date": event.original_delivery_date.isoformat() if event and event.original_delivery_date else None,
        "revised_delivery_date": event.revised_delivery_date.isoformat() if event and event.revised_delivery_date else None,
        "inventory_analysis": case.inventory_analysis,
        "impact": case.impact,
        "supplier_options": case.supplier_options,
        "mitigation": case.mitigation,
        "review": case.review,
        "revision_count": case.revision_count,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }


@router.get("/disruptions/events")
def list_events(session: Session = Depends(get_session)):
    return session.exec(select(DisruptionEventRecord).order_by(DisruptionEventRecord.detected_at.desc())).all()


@router.get("/disruptions/cases")
def list_cases(session: Session = Depends(get_session)):
    cases = session.exec(select(DisruptionCase).order_by(DisruptionCase.updated_at.desc())).all()
    return [_case_to_dict(session, c) for c in cases]


@router.get("/disruptions/cases/{case_number}")
def get_case(case_number: str, session: Session = Depends(get_session)):
    case = session.exec(select(DisruptionCase).where(DisruptionCase.case_number == case_number)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return _case_to_dict(session, case)


@router.get("/disruptions/cases/{case_number}/trace")
def get_case_trace(case_number: str, session: Session = Depends(get_session)):
    """The Context Lake, in order: exactly what each agent read, concluded, and cited as
    evidence for this case - the raw material behind 'explainable recommendations' rather
    than a claim taken on faith."""
    case = session.exec(select(DisruptionCase).where(DisruptionCase.case_number == case_number)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    entries = session.exec(
        select(AgentDecisionLog).where(AgentDecisionLog.case_id == case.id).order_by(AgentDecisionLog.created_at.asc())
    ).all()
    return [
        {
            "agent_name": e.agent_name,
            "input_summary": e.input_summary,
            "output_summary": e.output_summary,
            "evidence": e.evidence,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]


@router.get("/alerts")
def list_alerts(session: Session = Depends(get_session)):
    return session.exec(select(Alert).order_by(Alert.updated_at.desc())).all()
