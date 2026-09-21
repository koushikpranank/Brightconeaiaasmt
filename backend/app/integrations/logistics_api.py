"""Simulated Logistics/Freight Tracking API."""
from typing import Optional

from sqlmodel import Session, select

from app.models import LogisticsUpdate


def get_latest_tracking(session: Session, po_number: str) -> Optional[dict]:
    update = session.exec(
        select(LogisticsUpdate)
        .where(LogisticsUpdate.po_number == po_number)
        .order_by(LogisticsUpdate.reported_at.desc())
    ).first()
    if not update:
        return None
    return {
        "po_number": update.po_number,
        "carrier": update.carrier,
        "status": update.status,
        "location": update.location,
        "eta": update.eta.isoformat() if update.eta else None,
        "delay_days": update.delay_days,
        "source": update.source,
        "reported_at": update.reported_at.isoformat(),
    }


def list_delayed_shipments(session: Session) -> list[dict]:
    updates = session.exec(select(LogisticsUpdate).where(LogisticsUpdate.delay_days > 0)).all()
    return [
        {
            "po_number": u.po_number,
            "carrier": u.carrier,
            "status": u.status,
            "delay_days": u.delay_days,
            "eta": u.eta.isoformat() if u.eta else None,
        }
        for u in updates
    ]
