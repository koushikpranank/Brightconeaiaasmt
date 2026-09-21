"""Agent 1 - Supply Chain Monitoring Agent.

Two responsibilities split across two entry points:
  * `scan_for_changes` - the broad sweep across every simulated data source, run on a
    schedule (or on demand), producing raw candidate signals worth investigating.
  * `node` - the graph node that re-confirms one candidate signal's current status
    (supplier, delivery, logistics, weather) immediately before Detection reasons about it,
    so Detection never acts on stale data.
"""
from sqlmodel import Session, select

from app.agents.state import CaseState, log_step
from app.config import settings
from app.integrations import inventory_api, logistics_api, supplier_api, weather_api
from app.models import LogisticsUpdate, PurchaseOrder, Supplier


def scan_for_changes(session: Session) -> list[dict]:
    """Sweeps supplier/delivery/inventory/logistics sources for anything that looks like
    it needs investigation. Returns candidate signals, NOT confirmed disruptions -
    Detection Agent decides that."""
    candidates: list[dict] = []

    delayed_pos = session.exec(select(PurchaseOrder).where(PurchaseOrder.status == "delayed")).all()
    materials_already_flagged = {po.material for po in delayed_pos}
    for po in delayed_pos:
        candidates.append(
            {
                "kind": "supplier_delay",
                "po_number": po.po_number,
                "material": po.material,
                "supplier_code": po.supplier_code,
            }
        )

    delayed_shipments = logistics_api.list_delayed_shipments(session)
    for shipment in delayed_shipments:
        candidates.append(
            {
                "kind": "shipment_delay",
                "po_number": shipment["po_number"],
                "material": None,
                "supplier_code": None,
            }
        )

    # Skip a redundant "low inventory" signal for a material that already has its own
    # delayed PO under investigation - that case's own Inventory Agent step already covers
    # coverage/stockout math against the delay, so a second parallel case would be noise.
    low_coverage = inventory_api.list_low_coverage_materials(session)
    for item in low_coverage:
        if item["material"] in materials_already_flagged:
            continue
        candidates.append({"kind": "low_inventory", "po_number": None, "material": item["material"], "supplier_code": None})

    unavailable_suppliers = session.exec(select(Supplier).where(Supplier.status == "unavailable")).all()
    for s in unavailable_suppliers:
        candidates.append(
            {"kind": "supplier_unavailable", "po_number": None, "material": s.material, "supplier_code": s.supplier_code}
        )

    # A supplier whose quoted lead time has crept up well past what's on file is a risk signal
    # even with no active delay yet - Requirement 3's "unusual lead-time increase" type.
    active_suppliers = session.exec(select(Supplier).where(Supplier.status == "active")).all()
    for s in active_suppliers:
        if s.lead_time_days is None or s.baseline_lead_time_days in (None, 0):
            continue
        increase_ratio = (s.lead_time_days - s.baseline_lead_time_days) / s.baseline_lead_time_days
        if increase_ratio >= settings.lead_time_increase_threshold:
            candidates.append(
                {"kind": "lead_time_increase", "po_number": None, "material": s.material, "supplier_code": s.supplier_code}
            )

    return candidates


def node(state: CaseState, session: Session) -> dict:
    material = state["material"]
    po_number = state.get("source", "").replace("po:", "") if state.get("source", "").startswith("po:") else None

    observations: dict = {}

    if po_number:
        observations["delivery_status"] = supplier_api.get_delivery_status(session, po_number)
        observations["logistics"] = logistics_api.get_latest_tracking(session, po_number)

    observations["inventory_snapshot"] = inventory_api.get_inventory_snapshot(session, material)

    supplier_code = state.get("_supplier_code")
    if supplier_code:
        supplier_status = supplier_api.get_supplier_status(session, supplier_code)
        observations["supplier_status"] = supplier_status
        if supplier_status and supplier_status.get("material"):
            lat = state.get("_region_lat")
            lon = state.get("_region_lon")
            if lat is not None and lon is not None:
                observations["weather_risk"] = weather_api.get_weather_risk(lat, lon)

    updates = {
        "_observations": observations,
    }
    updates.update(
        log_step(
            state,
            "Supply Chain Monitoring Agent",
            input_summary=f"Re-checked live status for material={material}, po={po_number}, supplier={supplier_code}",
            output_summary="Collected current supplier/delivery/inventory/logistics observations",
            evidence=observations,
        )
    )
    return updates
