"""Simulated Supplier API.

Stands in for a real supplier portal/EDI feed. Shaped as an external API client would be:
functions take identifiers and return plain dict payloads, not ORM objects, so swapping this
module for a real HTTP client later doesn't touch any agent code.
"""
from typing import Optional

from sqlmodel import Session, select

from app.models import PurchaseOrder, Supplier


def get_supplier_status(session: Session, supplier_code: str) -> Optional[dict]:
    supplier = session.exec(select(Supplier).where(Supplier.supplier_code == supplier_code)).first()
    if not supplier:
        return None
    return {
        "supplier_code": supplier.supplier_code,
        "name": supplier.name,
        "material": supplier.material,
        "status": supplier.status,
        "lead_time_days": supplier.lead_time_days,
        "baseline_lead_time_days": supplier.baseline_lead_time_days,
        "price_per_unit": supplier.price_per_unit,
        "available_quantity": supplier.available_quantity,
        "capacity_units_per_month": supplier.capacity_units_per_month,
        "approved": supplier.approved,
        "capacity_notes": supplier.capacity_notes,
    }


def list_approved_suppliers(session: Session, material: str, exclude_supplier_code: Optional[str] = None) -> list[dict]:
    query = select(Supplier).where(Supplier.material == material, Supplier.approved == True)  # noqa: E712
    suppliers = session.exec(query).all()
    return [
        {
            "supplier_code": s.supplier_code,
            "name": s.name,
            "material": s.material,
            "status": s.status,
            "lead_time_days": s.lead_time_days,
            "price_per_unit": s.price_per_unit,
            "available_quantity": s.available_quantity,
            "capacity_units_per_month": s.capacity_units_per_month,
            "approved": s.approved,
            "capacity_notes": s.capacity_notes,
        }
        for s in suppliers
        if s.supplier_code != exclude_supplier_code
    ]


def get_delivery_status(session: Session, po_number: str) -> Optional[dict]:
    po = session.exec(select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)).first()
    if not po:
        return None
    return {
        "po_number": po.po_number,
        "material": po.material,
        "supplier_code": po.supplier_code,
        "quantity": po.quantity,
        "original_delivery_date": po.original_delivery_date.isoformat(),
        "revised_delivery_date": po.revised_delivery_date.isoformat() if po.revised_delivery_date else None,
        "status": po.status,
    }


def announce_delay(session: Session, po_number: str, delay_days: int, reason: str) -> dict:
    """Simulates the supplier portal pushing a delay notice for an open PO."""
    from datetime import timedelta

    po = session.exec(select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)).first()
    if not po:
        raise ValueError(f"Unknown purchase order {po_number}")

    po.revised_delivery_date = po.original_delivery_date + timedelta(days=delay_days)
    po.status = "delayed"
    session.add(po)
    session.commit()
    session.refresh(po)

    return {
        "po_number": po.po_number,
        "material": po.material,
        "supplier_code": po.supplier_code,
        "original_delivery_date": po.original_delivery_date.isoformat(),
        "revised_delivery_date": po.revised_delivery_date.isoformat(),
        "delay_days": delay_days,
        "reason": reason,
    }


def announce_lead_time_increase(session: Session, supplier_code: str, new_lead_time_days: int) -> dict:
    """Simulates the supplier's portal quoting a longer lead time than what's on file."""
    supplier = session.exec(select(Supplier).where(Supplier.supplier_code == supplier_code)).first()
    if not supplier:
        raise ValueError(f"Unknown supplier {supplier_code}")

    if supplier.baseline_lead_time_days is None:
        supplier.baseline_lead_time_days = supplier.lead_time_days
    supplier.lead_time_days = new_lead_time_days
    session.add(supplier)
    session.commit()
    session.refresh(supplier)

    return {
        "supplier_code": supplier.supplier_code,
        "material": supplier.material,
        "baseline_lead_time_days": supplier.baseline_lead_time_days,
        "lead_time_days": supplier.lead_time_days,
    }


def restore_lead_time(session: Session, supplier_code: str) -> dict:
    """Simulates the supplier's quoted lead time returning to its on-file baseline."""
    supplier = session.exec(select(Supplier).where(Supplier.supplier_code == supplier_code)).first()
    if not supplier:
        raise ValueError(f"Unknown supplier {supplier_code}")

    if supplier.baseline_lead_time_days is not None:
        supplier.lead_time_days = supplier.baseline_lead_time_days
    session.add(supplier)
    session.commit()
    session.refresh(supplier)

    return {
        "supplier_code": supplier.supplier_code,
        "material": supplier.material,
        "lead_time_days": supplier.lead_time_days,
    }
