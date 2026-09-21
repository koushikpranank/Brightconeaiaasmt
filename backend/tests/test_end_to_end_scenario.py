"""End-to-end pipeline tests mirroring the spec's Testing Requirements table (TC-01..TC-05),
plus the lead-time-increase disruption type and the differentiated human-approval categories."""
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.integrations.supplier_api import announce_delay, announce_lead_time_increase, restore_lead_time
from app.models import ActionItem, Alert, ApprovalRequest, DisruptionCase, InventoryItem, ProductionOrder, Supplier
from app.services.case_runner import run_monitoring_sweep


def test_tc01_supplier_delay_produces_alert_and_approval(steel_plate_scenario: Session):
    session = steel_plate_scenario
    announce_delay(session, "PO-1001", 10, "supplier announced a 10-day delay")

    cases = run_monitoring_sweep(session)
    assert len(cases) == 1
    case = cases[0]

    assert case.status in ("pending_approval", "needs_revision")
    assert case.inventory_analysis["coverage_days"] == 5.0
    assert case.inventory_analysis["projected_stockout_date"] == "2026-09-24"
    assert case.impact["severity"] != "unknown"
    assert case.impact["estimated_delay_days"] == 10
    assert "PROD-500" in case.impact["affected_production_orders"]

    best_option = case.mitigation["options"][0]
    assert best_option["supplier_code"] == "SUP-002"  # 7-day lead time beats SUP-001's 15
    assert best_option["data_confidence"] == "confirmed"

    alert = session.exec(select(Alert)).first()
    assert alert is not None
    assert alert.disruption_type == "supplier_delay"
    assert alert.status == "open"

    approval = session.exec(select(ApprovalRequest)).first()
    assert approval is not None
    assert approval.status == "pending"
    # A confirmed alternative supplier exists for a supplier_delay -> approval is specifically
    # "change_supplier", not a generic catch-all (Requirement 9's four distinct categories).
    assert approval.action_type == "change_supplier"
    assert "Alpha Metals" in approval.description

    actions = session.exec(select(ActionItem)).all()
    assert len(actions) > 0


def test_tc01_duplicate_sweep_does_not_duplicate_alert(steel_plate_scenario: Session):
    session = steel_plate_scenario
    announce_delay(session, "PO-1001", 10, "supplier announced a 10-day delay")

    run_monitoring_sweep(session)
    run_monitoring_sweep(session)

    alerts = session.exec(select(Alert)).all()
    assert len(alerts) == 1
    assert alerts[0].occurrence_count >= 2

    cases = session.exec(select(DisruptionCase)).all()
    assert len(cases) == 1  # same case reused, not duplicated


def test_tc02_inventory_below_threshold_triggers_shortage_alert(session: Session):
    session.add(
        Supplier(
            supplier_code="SUP-010",
            name="Bright Copper Co",
            material="Copper Wire",
            lead_time_days=5,
            price_per_unit=120,
            available_quantity=500,
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
            snapshot_at=datetime.utcnow(),
        )
    )
    session.commit()

    cases = run_monitoring_sweep(session)
    assert len(cases) == 1
    assert cases[0].impact  # impact assessment ran
    alert = session.exec(select(Alert)).first()
    assert alert.disruption_type == "shortage"
    assert alert.material == "Copper Wire"


def test_tc03_alternative_supplier_available_is_confirmed(steel_plate_scenario: Session):
    session = steel_plate_scenario
    announce_delay(session, "PO-1001", 10, "delay")
    cases = run_monitoring_sweep(session)
    options = cases[0].mitigation["options"]
    assert any(o["data_confidence"] == "confirmed" and o["supplier_code"] == "SUP-002" for o in options)


def test_tc04_no_supplier_availability_requires_verification(session: Session):
    session.add(
        Supplier(
            supplier_code="SUP-020",
            name="Seal & Gasket Works",
            material="Rubber Gasket",
            lead_time_days=6,
            price_per_unit=15,
            available_quantity=1000,
            approved=True,
            is_primary=True,
            status="unavailable",
        )
    )
    session.add(
        Supplier(
            supplier_code="SUP-021",
            name="Unverified Rubber Traders",
            material="Rubber Gasket",
            lead_time_days=None,
            price_per_unit=None,
            available_quantity=None,
            approved=True,
            status="active",
        )
    )
    session.add(
        InventoryItem(
            material="Rubber Gasket",
            current_quantity=400,
            daily_consumption=10,
            reorder_point_days=10,
            snapshot_at=datetime.utcnow(),
        )
    )
    session.commit()

    cases = run_monitoring_sweep(session)
    assert len(cases) == 1
    mitigation = cases[0].mitigation
    assert "SUP-021" in mitigation["verification_needed"]
    assert mitigation["options"][0]["data_confidence"] == "requires_verification"


def test_lead_time_increase_detected_and_resolved(session: Session):
    """Requirement 3 / Agent 2's sixth disruption type: a supplier's quoted lead time
    growing well past its on-file baseline, with no other symptom present."""
    session.add(
        Supplier(
            supplier_code="SUP-040",
            name="Precision Bearing Corp",
            material="Industrial Bearings",
            lead_time_days=5,
            baseline_lead_time_days=5,
            price_per_unit=45,
            available_quantity=800,
            capacity_units_per_month=2000,
            approved=True,
            is_primary=True,
            status="active",
        )
    )
    session.add(
        InventoryItem(
            material="Industrial Bearings",
            current_quantity=500,
            daily_consumption=10,
            required_quantity=500,
            reorder_point_days=10,
            snapshot_at=datetime.utcnow(),
        )
    )
    session.commit()

    # Healthy at first: no candidate should be raised yet.
    assert run_monitoring_sweep(session) == []

    announce_lead_time_increase(session, "SUP-040", new_lead_time_days=12)  # +140% vs baseline
    cases = run_monitoring_sweep(session)
    assert len(cases) == 1
    assert cases[0].status in ("pending_approval", "needs_revision")

    alert = session.exec(select(Alert)).first()
    assert alert.disruption_type == "lead_time_increase"
    assert alert.material == "Industrial Bearings"
    assert alert.responsible_team == "Procurement"

    # Restoring the lead time resolves it, mirroring TC-05's restoration behavior.
    restore_lead_time(session, "SUP-040")
    run_monitoring_sweep(session)
    case = session.exec(select(DisruptionCase)).first()
    assert case.status == "resolved"


def test_approval_action_type_falls_back_to_modify_delivery_commitment_without_alternative(session: Session):
    """TC-04-style situation: no confirmed alternative supplier -> the approval must ask to
    revise the delivery commitment, not silently reuse another category."""
    session.add(
        Supplier(
            supplier_code="SUP-020",
            name="Seal & Gasket Works",
            material="Rubber Gasket",
            lead_time_days=6,
            price_per_unit=15,
            available_quantity=1000,
            approved=True,
            is_primary=True,
            status="unavailable",
        )
    )
    session.add(
        InventoryItem(
            material="Rubber Gasket",
            current_quantity=400,
            daily_consumption=10,
            reorder_point_days=10,
            snapshot_at=datetime.utcnow(),
        )
    )
    session.commit()

    run_monitoring_sweep(session)
    approval = session.exec(select(ApprovalRequest)).first()
    assert approval.action_type == "modify_delivery_commitment"


def test_tc05_delivery_restored_resolves_case(steel_plate_scenario: Session):
    from app.models import PurchaseOrder

    session = steel_plate_scenario
    announce_delay(session, "PO-1001", 10, "delay")
    run_monitoring_sweep(session)

    po = session.exec(select(PurchaseOrder).where(PurchaseOrder.po_number == "PO-1001")).first()
    po.revised_delivery_date = None
    po.status = "open"
    session.add(po)
    session.commit()

    run_monitoring_sweep(session)

    case = session.exec(select(DisruptionCase)).first()
    assert case.status == "resolved"
