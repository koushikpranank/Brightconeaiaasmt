"""SQLModel ORM models = the Postgres schema.

Every table an agent writes to also doubles as the "Context Lake": AgentDecisionLog and
EvidenceRecord give later agent runs (and the Reviewer) a queryable trail of what was
concluded before and why, instead of re-deriving or hallucinating it.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def now() -> datetime:
    return datetime.utcnow()


class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier_code: str = Field(index=True, unique=True)
    name: str
    material: str = Field(index=True)
    lead_time_days: Optional[int] = None
    baseline_lead_time_days: Optional[int] = None  # on-file reference lead time, used to detect unusual increases
    price_per_unit: Optional[float] = None
    currency: str = "USD"
    available_quantity: Optional[float] = None
    capacity_units_per_month: Optional[float] = None  # production/supply capacity, distinct from current on-hand stock
    capacity_notes: Optional[str] = None
    approved: bool = True
    is_primary: bool = False
    status: str = "active"  # active | unavailable | at_risk
    last_verified_at: Optional[datetime] = None
    region_lat: Optional[float] = None
    region_lon: Optional[float] = None


class InventoryItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    material: str = Field(index=True, unique=True)
    unit: str = "tonnes"
    current_quantity: float
    daily_consumption: float
    required_quantity: Optional[float] = None  # total quantity needed for the active order/production cycle
    reorder_point_days: float = 10
    snapshot_at: Optional[datetime] = None  # inventory timestamp - required for stockout math


class PurchaseOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    po_number: str = Field(index=True, unique=True)
    material: str = Field(index=True)
    supplier_code: str
    quantity: float
    original_delivery_date: date
    revised_delivery_date: Optional[date] = None
    status: str = "open"  # open | delayed | fulfilled | cancelled


class ProductionOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_number: str = Field(index=True, unique=True)
    material: str = Field(index=True)
    quantity_required: float
    due_date: date
    customer: str
    status: str = "scheduled"  # scheduled | at_risk | delayed | completed


class LogisticsUpdate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    po_number: str = Field(index=True)
    carrier: Optional[str] = None
    status: str = "in_transit"
    location: Optional[str] = None
    eta: Optional[date] = None
    delay_days: int = 0
    source: str = "logistics_api"
    reported_at: datetime = Field(default_factory=now)


class DisruptionEventRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_ref: str = Field(index=True)  # id of the source record (PO number, supplier code, etc.)
    material: str = Field(index=True)
    disruption_type: str  # supplier_delay | shipment_delay | shortage | lead_time_increase | supplier_unavailable
    source: str
    description: str
    original_delivery_date: Optional[date] = None
    revised_delivery_date: Optional[date] = None
    raw_payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    detected_at: datetime = Field(default_factory=now)


class DisruptionCase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_number: str = Field(index=True, unique=True)
    event_id: int = Field(foreign_key="disruptioneventrecord.id")
    status: str = "in_progress"
    # active | pending_approval | approved | rejected | resolved | needs_revision
    inventory_analysis: dict = Field(default_factory=dict, sa_column=Column(JSON))
    impact: dict = Field(default_factory=dict, sa_column=Column(JSON))
    supplier_options: list = Field(default_factory=list, sa_column=Column(JSON))
    mitigation: dict = Field(default_factory=dict, sa_column=Column(JSON))
    review: dict = Field(default_factory=dict, sa_column=Column(JSON))
    revision_count: int = 0
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dedup_key: str = Field(index=True, unique=True)
    case_id: int = Field(foreign_key="disruptioncase.id")
    disruption_type: str
    material: str
    source: str
    expected_impact: str
    recommended_action: str
    responsible_team: str
    status: str = "open"  # open | updated | resolved
    occurrence_count: int = 1
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class ApprovalRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="disruptioncase.id")
    action_type: str  # place_purchase_order | change_supplier | commit_expenditure | modify_delivery_commitment
    description: str
    estimated_cost: Optional[float] = None
    status: str = "pending"  # pending | approved | rejected
    requested_at: datetime = Field(default_factory=now)
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    notes: Optional[str] = None


class ActionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="disruptioncase.id")
    description: str
    responsible_team: str
    status: str = "open"  # open | in_progress | done
    due_date: Optional[date] = None
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class AgentDecisionLog(SQLModel, table=True):
    """Context Lake entry: one row per agent step, queryable by later agents/the reviewer."""

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="disruptioncase.id")
    agent_name: str
    input_summary: str
    output_summary: str
    evidence: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now)


class EvidenceRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="disruptioncase.id")
    source: str
    content: str
    created_at: datetime = Field(default_factory=now)
