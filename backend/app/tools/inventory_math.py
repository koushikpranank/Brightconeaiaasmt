"""Deterministic inventory/demand calculations.

These are plain functions, not LLM calls. Agents invoke them as tools and the Reviewer
Agent re-invokes the same functions independently to verify any number that appears in a
case. Nothing here fabricates a date: if the inventory snapshot timestamp is missing, the
stockout date is deliberately left as None with a note explaining why, per the spec's
"It should not invent the stockout date if the inventory snapshot date is unavailable."
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional


@dataclass
class InventoryCoverageResult:
    coverage_days: Optional[float]
    projected_stockout_date: Optional[date]
    stockout_calculable: bool
    reorder_required: bool
    notes: list[str] = field(default_factory=list)


def calculate_inventory_coverage(
    current_quantity: float,
    daily_consumption: float,
    snapshot_at: Optional[datetime],
    reorder_point_days: float,
    revised_delivery_date: Optional[date] = None,
) -> InventoryCoverageResult:
    notes: list[str] = []

    if daily_consumption <= 0:
        notes.append("Daily consumption is zero or negative; coverage is undefined.")
        return InventoryCoverageResult(None, None, False, False, notes)

    coverage_days = round(current_quantity / daily_consumption, 2)

    if snapshot_at is None:
        notes.append(
            "Inventory snapshot timestamp is unavailable; stockout date cannot be derived "
            "and has deliberately been left blank rather than estimated."
        )
        stockout_date = None
        calculable = False
    else:
        stockout_date = (snapshot_at.date() if isinstance(snapshot_at, datetime) else snapshot_at) + timedelta(
            days=coverage_days
        )
        calculable = True

    reorder_required = coverage_days <= reorder_point_days

    if calculable and revised_delivery_date and stockout_date < revised_delivery_date:
        gap_days = (revised_delivery_date - stockout_date).days
        notes.append(
            f"Projected stockout ({stockout_date.isoformat()}) precedes the revised delivery "
            f"date ({revised_delivery_date.isoformat()}) by {gap_days} day(s): a coverage gap exists."
        )

    return InventoryCoverageResult(
        coverage_days=coverage_days,
        projected_stockout_date=stockout_date,
        stockout_calculable=calculable,
        reorder_required=reorder_required,
        notes=notes,
    )


def calculate_delay_impact(
    original_delivery_date: date,
    revised_delivery_date: date,
) -> int:
    """Positive integer number of days the delivery has slipped."""
    return max(0, (revised_delivery_date - original_delivery_date).days)


def calculate_mitigation_window(
    projected_stockout_date: Optional[date],
    reference_date: date,
) -> Optional[int]:
    """Days available to act before the material actually runs out. None if stockout
    date could not be calculated (missing snapshot)."""
    if projected_stockout_date is None:
        return None
    return (projected_stockout_date - reference_date).days


def classify_severity(mitigation_window_days: Optional[int], coverage_days: Optional[float]) -> str:
    if mitigation_window_days is None or coverage_days is None:
        return "unknown"
    if mitigation_window_days < 0:
        return "critical"
    if mitigation_window_days <= 3:
        return "high"
    if mitigation_window_days <= 10:
        return "medium"
    return "low"


def build_dedup_key(material: str, disruption_type: str, source_event_ref: str) -> str:
    return f"{material}|{disruption_type}|{source_event_ref}".lower().replace(" ", "_")
