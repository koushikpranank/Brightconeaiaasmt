"""Seeds a demo dataset built around the spec's steel-plate scenario, plus a handful of
extra materials so the dashboard and every test case (TC-01..TC-05, plus the lead-time-increase
scenario) have real data to work against instead of an empty database.
"""
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.database import engine
from app.models import InventoryItem, ProductionOrder, PurchaseOrder, Supplier


def seed() -> None:
    with Session(engine) as session:
        if session.exec(select(Supplier)).first():
            return  # already seeded

        today = date.today()

        # --- Steel Plate: the spec's worked example (TC-01, TC-03) ---
        session.add_all(
            [
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
                    region_lat=40.44,
                    region_lon=-79.99,
                ),
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
                ),
                Supplier(
                    supplier_code="SUP-003",
                    name="Global Steel Partners",
                    material="Steel Plate",
                    lead_time_days=10,
                    baseline_lead_time_days=10,
                    price_per_unit=790,
                    available_quantity=None,  # quote outstanding -> requires_verification
                    capacity_units_per_month=None,  # capacity not yet confirmed either
                    approved=True,
                    status="active",
                    capacity_notes="Quantity and capacity not yet confirmed by supplier.",
                ),
            ]
        )
        session.add(
            InventoryItem(
                material="Steel Plate",
                current_quantity=25,
                daily_consumption=5,
                required_quantity=100,
                reorder_point_days=10,
                snapshot_at=datetime(today.year, today.month, today.day, 8, 0, 0),
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
        session.add_all(
            [
                ProductionOrder(
                    order_number="PROD-500",
                    material="Steel Plate",
                    quantity_required=100,
                    due_date=date(2026, 9, 25),
                    customer="Acme Fabrication Co",
                    status="scheduled",
                ),
                ProductionOrder(
                    order_number="PROD-501",
                    material="Steel Plate",
                    quantity_required=60,
                    due_date=date(2026, 10, 2),
                    customer="Beta Construction",
                    status="scheduled",
                ),
            ]
        )

        # --- Copper Wire: already below reorder threshold -> auto-detected shortage (TC-02) ---
        session.add(
            Supplier(
                supplier_code="SUP-010",
                name="Bright Copper Co",
                material="Copper Wire",
                lead_time_days=5,
                baseline_lead_time_days=5,
                price_per_unit=120,
                available_quantity=500,
                capacity_units_per_month=2000,
                approved=True,
                is_primary=True,
                status="active",
            )
        )
        session.add(
            Supplier(
                supplier_code="SUP-011",
                name="Meridian Wire Supply",
                material="Copper Wire",
                lead_time_days=4,
                baseline_lead_time_days=4,
                price_per_unit=125,
                available_quantity=300,
                capacity_units_per_month=1200,
                approved=True,
                status="active",
            )
        )
        session.add(
            InventoryItem(
                material="Copper Wire",
                current_quantity=20,
                daily_consumption=4,
                required_quantity=80,
                reorder_point_days=10,
                snapshot_at=datetime(today.year, today.month, today.day, 8, 0, 0),
            )
        )
        session.add(
            ProductionOrder(
                order_number="PROD-600",
                material="Copper Wire",
                quantity_required=80,
                due_date=today + timedelta(days=6),
                customer="Volt Electronics",
                status="scheduled",
            )
        )

        # --- Rubber Gasket: primary supplier unavailable, no approved alternative on file
        #     -> mitigation must say "verification required", never invent one (TC-04) ---
        session.add(
            Supplier(
                supplier_code="SUP-020",
                name="Seal & Gasket Works",
                material="Rubber Gasket",
                lead_time_days=6,
                baseline_lead_time_days=6,
                price_per_unit=15,
                available_quantity=1000,
                capacity_units_per_month=5000,
                approved=True,
                is_primary=True,
                status="unavailable",
                capacity_notes="Plant closure reported; no ship date provided.",
            )
        )
        session.add(
            InventoryItem(
                material="Rubber Gasket",
                current_quantity=400,
                daily_consumption=10,
                required_quantity=None,
                reorder_point_days=10,
                snapshot_at=datetime(today.year, today.month, today.day, 8, 0, 0),
            )
        )

        # --- Aluminum Coil: healthy baseline, nothing wrong (control case) ---
        session.add(
            Supplier(
                supplier_code="SUP-030",
                name="Northline Aluminum",
                material="Aluminum Coil",
                lead_time_days=6,
                baseline_lead_time_days=6,
                price_per_unit=340,
                available_quantity=200,
                capacity_units_per_month=800,
                approved=True,
                is_primary=True,
                status="active",
            )
        )
        session.add(
            InventoryItem(
                material="Aluminum Coil",
                current_quantity=180,
                daily_consumption=6,
                required_quantity=100,
                reorder_point_days=10,
                snapshot_at=datetime(today.year, today.month, today.day, 8, 0, 0),
            )
        )
        session.add(
            PurchaseOrder(
                po_number="PO-2001",
                material="Aluminum Coil",
                supplier_code="SUP-030",
                quantity=100,
                original_delivery_date=today + timedelta(days=14),
                status="open",
            )
        )

        # --- Industrial Bearings: primary supplier's quoted lead time has crept up well
        #     beyond what's on file, with healthy stock otherwise -> isolates the
        #     "unusual lead-time increase" disruption type (Requirement 3 / Agent 2) so it is
        #     detected on its own, not bundled with a shortage or delay signal. ---
        session.add_all(
            [
                Supplier(
                    supplier_code="SUP-040",
                    name="Precision Bearing Corp",
                    material="Industrial Bearings",
                    lead_time_days=12,
                    baseline_lead_time_days=5,  # quoted lead time has more than doubled since it was approved
                    price_per_unit=45,
                    available_quantity=800,
                    capacity_units_per_month=2000,
                    approved=True,
                    is_primary=True,
                    status="active",
                ),
                Supplier(
                    supplier_code="SUP-041",
                    name="FastTrack Bearings",
                    material="Industrial Bearings",
                    lead_time_days=4,
                    baseline_lead_time_days=4,
                    price_per_unit=48,
                    available_quantity=600,
                    capacity_units_per_month=1500,
                    approved=True,
                    status="active",
                ),
            ]
        )
        session.add(
            InventoryItem(
                material="Industrial Bearings",
                current_quantity=500,
                daily_consumption=10,
                required_quantity=500,
                reorder_point_days=10,
                snapshot_at=datetime(today.year, today.month, today.day, 8, 0, 0),
            )
        )
        session.add(
            ProductionOrder(
                order_number="PROD-700",
                material="Industrial Bearings",
                quantity_required=500,
                due_date=today + timedelta(days=20),
                customer="Precision Motors Inc",
                status="scheduled",
            )
        )

        session.commit()
