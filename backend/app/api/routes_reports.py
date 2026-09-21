from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session, select

from app.database import get_session
from app.models import Alert, ApprovalRequest, DisruptionCase, DisruptionEventRecord
from app.reports.pdf_generator import build_case_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def _load(session: Session, case_number: str):
    case = session.exec(select(DisruptionCase).where(DisruptionCase.case_number == case_number)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    event = session.get(DisruptionEventRecord, case.event_id)
    alert = session.exec(select(Alert).where(Alert.case_id == case.id)).first()
    approval = session.exec(
        select(ApprovalRequest).where(ApprovalRequest.case_id == case.id).order_by(ApprovalRequest.requested_at.desc())
    ).first()
    return case, event, alert, approval


@router.get("/{case_number}")
def get_report_json(case_number: str, session: Session = Depends(get_session)):
    case, event, alert, approval = _load(session, case_number)
    return {
        "case_number": case.case_number,
        "status": case.status,
        "event": event,
        "inventory_analysis": case.inventory_analysis,
        "impact": case.impact,
        "mitigation": case.mitigation,
        "review": case.review,
        "alert": alert,
        "approval": approval,
    }


@router.get("/{case_number}/pdf")
def get_report_pdf(case_number: str, session: Session = Depends(get_session)):
    case, event, alert, approval = _load(session, case_number)
    pdf_bytes = build_case_report_pdf(case, event, alert, approval)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{case_number}_report.pdf"'},
    )
