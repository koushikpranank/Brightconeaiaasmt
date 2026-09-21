"""Request/response contracts that aren't just the ORM models themselves."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class SupplierDelayEventIn(BaseModel):
    """Payload used to simulate an inbound supplier/logistics disruption signal."""

    po_number: str
    material: str
    supplier_code: str
    delay_days: int
    reason: Optional[str] = "supplier announced delay"


class LeadTimeIncreaseEventIn(BaseModel):
    """Payload used to simulate a supplier quoting a longer lead time than what's on file."""

    supplier_code: str
    new_lead_time_days: int


class ApprovalDecisionIn(BaseModel):
    approver: str
    decision: str  # "approved" | "rejected"
    notes: Optional[str] = None


class ActionItemUpdateIn(BaseModel):
    status: str  # open | in_progress | done


class MonitorRunResult(BaseModel):
    checked_at: str
    changes_detected: int
    cases_created: list[str]


class CaseSummaryOut(BaseModel):
    case_number: str
    material: str
    disruption_type: str
    status: str
    severity: Optional[str] = None
    created_at: str
    updated_at: str
