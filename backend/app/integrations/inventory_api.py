"""Simulated Inventory Management API (e.g. stand-in for an ERP/WMS feed)."""
from typing import Optional

from sqlmodel import Session, select

from app.models import InventoryItem


def get_inventory_snapshot(session: Session, material: str) -> Optional[dict]:
    item = session.exec(select(InventoryItem).where(InventoryItem.material == material)).first()
    if not item:
        return None
    return {
        "material": item.material,
        "unit": item.unit,
        "current_quantity": item.current_quantity,
        "daily_consumption": item.daily_consumption,
        "reorder_point_days": item.reorder_point_days,
        "snapshot_at": item.snapshot_at.isoformat() if item.snapshot_at else None,
    }


def list_low_coverage_materials(session: Session) -> list[dict]:
    items = session.exec(select(InventoryItem)).all()
    results = []
    for item in items:
        if item.daily_consumption <= 0:
            continue
        coverage_days = item.current_quantity / item.daily_consumption
        if coverage_days <= item.reorder_point_days:
            results.append({"material": item.material, "coverage_days": round(coverage_days, 2)})
    return results
