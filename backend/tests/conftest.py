from datetime import date, datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models import InventoryItem, ProductionOrder, PurchaseOrder, Supplier


@pytest.fixture()
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture()
def steel_plate_scenario(session: Session):
    """Seeds exactly the spec's worked example: 100t required, 25t on hand, 5t/day burn,
    original delivery 2026-09-20, an alternate supplier with a 7-day lead time."""
    session.add(
        Supplier(
            supplier_code="SUP-001",
            name="SteelCorp Industries",
            material="Steel Plate",
            lead_time_days=15,
            baseline_lead_time_days=15,
            price_per_unit=800,
            available_quantity=150,
            capacity_units_per_month=500,
            approved=True,
            is_primary=True,
            status="active",
        )
    )
    session.add(
        Supplier(
            supplier_code="SUP-002",
            name="Alpha Metals Ltd",
            material="Steel Plate",
            lead_time_days=7,
            baseline_lead_time_days=7,
            price_per_unit=850,
            available_quantity=120,
            capacity_units_per_month=300,
            approved=True,
            status="active",
        )
    )
    session.add(
        InventoryItem(
            material="Steel Plate",
            current_quantity=25,
            daily_consumption=5,
            required_quantity=100,
            reorder_point_days=10,
            snapshot_at=datetime(2026, 9, 19, 8, 0, 0),
        )
    )
    session.add(
        PurchaseOrder(
            po_number="PO-1001",
            material="Steel Plate",
            supplier_code="SUP-001",
            quantity=100,
            original_delivery_date=date(2026, 9, 20),
            status="open",
        )
    )
    session.add(
        ProductionOrder(
            order_number="PROD-500",
            material="Steel Plate",
            quantity_required=100,
            due_date=date(2026, 9, 25),
            customer="Acme Fabrication Co",
            status="scheduled",
        )
    )
    session.commit()
    return session
