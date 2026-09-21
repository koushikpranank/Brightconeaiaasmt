"""Deterministic supplier comparison. Never invents a supplier, price, or quantity -
it only ranks what the (simulated) supplier data source actually returned.

Evaluates all four dimensions Requirement 6 names explicitly: lead time, price,
available quantity (material availability), and capacity - plus approval status.
Capacity is a supplier's ongoing production/supply rate and is judged separately from
available_quantity (their current on-hand stock): a supplier can have plenty on the shelf
today but not enough monthly capacity to keep a plant supplied going forward, or vice versa.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SupplierScore:
    supplier_code: str
    name: str
    lead_time_days: Optional[int]
    price_per_unit: Optional[float]
    available_quantity: Optional[float]
    capacity_units_per_month: Optional[float]
    approved: bool
    meets_quantity: Optional[bool]
    meets_capacity: Optional[bool]
    data_confidence: str  # "confirmed" | "requires_verification"
    rank_score: Optional[float]


def score_supplier(
    supplier_code: str,
    name: str,
    lead_time_days: Optional[int],
    price_per_unit: Optional[float],
    available_quantity: Optional[float],
    approved: bool,
    capacity_units_per_month: Optional[float] = None,
    required_quantity: Optional[float] = None,
) -> SupplierScore:
    has_full_data = (
        lead_time_days is not None
        and price_per_unit is not None
        and available_quantity is not None
        and capacity_units_per_month is not None
    )
    confidence = "confirmed" if has_full_data else "requires_verification"

    meets_quantity = None
    if available_quantity is not None and required_quantity is not None:
        meets_quantity = available_quantity >= required_quantity

    meets_capacity = None
    if capacity_units_per_month is not None and required_quantity is not None:
        meets_capacity = capacity_units_per_month >= required_quantity

    rank_score = None
    if has_full_data:
        # Lower is better: normalize lead time (days) and price into one comparable score.
        rank_score = round(lead_time_days * 1.0 + price_per_unit * 0.1, 2)

    return SupplierScore(
        supplier_code=supplier_code,
        name=name,
        lead_time_days=lead_time_days,
        price_per_unit=price_per_unit,
        available_quantity=available_quantity,
        capacity_units_per_month=capacity_units_per_month,
        approved=approved,
        meets_quantity=meets_quantity,
        meets_capacity=meets_capacity,
        data_confidence=confidence,
        rank_score=rank_score,
    )


def rank_suppliers(scores: list[SupplierScore]) -> list[SupplierScore]:
    confirmed = [s for s in scores if s.rank_score is not None]
    unconfirmed = [s for s in scores if s.rank_score is None]
    confirmed.sort(key=lambda s: s.rank_score)
    return confirmed + unconfirmed
