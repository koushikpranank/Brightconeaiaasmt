from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.services.analytics import build_summary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(session: Session = Depends(get_session)):
    """Pandas-computed historical trends across every disruption case and alert ever
    recorded - frequency by material, severity mix, mitigation-window averages, alert
    load by team, and a recent-activity timeline."""
    return build_summary(session)
