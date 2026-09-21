"""Agent 2 - Disruption Detection Agent.

Turns a raw monitored signal into a structured, confirmed disruption event: compares
planned vs. revised dates, checks inventory against threshold, and classifies the type.
If the underlying data no longer shows a problem (e.g. delivery date was restored), the
case is marked resolved here rather than proceeding through the rest of the pipeline -
covers TC-05 (delivery schedule restored -> updated disruption status).
"""
from datetime import date

from sqlmodel import Session

from app.agents.state import CaseState, log_step
from app.config import settings
from app.tools.inventory_math import calculate_delay_impact


def node(state: CaseState, session: Session) -> dict:
    observations = state.get("_observations", {})
    disruption_type = state["disruption_type"]
    confirmed = True
    notes: list[str] = []
    delay_days = 0

    delivery = observations.get("delivery_status")
    if disruption_type == "supplier_delay":
        if delivery and delivery.get("revised_delivery_date"):
            original = date.fromisoformat(delivery["original_delivery_date"])
            revised = date.fromisoformat(delivery["revised_delivery_date"])
            delay_days = calculate_delay_impact(original, revised)
            confirmed = delay_days > 0
            notes.append(f"Revised delivery date confirmed via supplier API: {delay_days} day(s) slip.")
        else:
            confirmed = False
            notes.append("Supplier API no longer reports a revised delivery date; delay appears resolved.")

    elif disruption_type == "shipment_delay":
        logistics = observations.get("logistics")
        if logistics and logistics.get("delay_days", 0) > 0:
            delay_days = logistics["delay_days"]
            notes.append(f"Logistics tracking confirms {delay_days} day(s) shipment delay.")
        else:
            confirmed = False
            notes.append("Logistics tracking no longer shows a delay.")

    elif disruption_type == "shortage" or disruption_type == "low_inventory":
        snapshot = observations.get("inventory_snapshot")
        if snapshot and snapshot.get("daily_consumption", 0) > 0:
            coverage = snapshot["current_quantity"] / snapshot["daily_consumption"]
            threshold = snapshot.get("reorder_point_days", settings.low_inventory_threshold_days)
            confirmed = coverage <= threshold
            notes.append(f"Current inventory coverage recalculated at {coverage:.1f} day(s) against a {threshold}-day threshold.")
            disruption_type = "shortage"
        else:
            confirmed = False

    elif disruption_type == "supplier_unavailable":
        supplier_status = observations.get("supplier_status")
        confirmed = bool(supplier_status and supplier_status.get("status") == "unavailable")
        notes.append("Supplier status re-confirmed as unavailable." if confirmed else "Supplier is available again.")

    elif disruption_type == "lead_time_increase":
        supplier_status = observations.get("supplier_status")
        if supplier_status and supplier_status.get("lead_time_days") is not None and supplier_status.get("baseline_lead_time_days"):
            current = supplier_status["lead_time_days"]
            baseline = supplier_status["baseline_lead_time_days"]
            increase_ratio = (current - baseline) / baseline
            confirmed = increase_ratio >= settings.lead_time_increase_threshold
            delay_days = max(0, current - baseline)
            notes.append(
                f"Quoted lead time re-checked at {current} day(s) vs a {baseline}-day baseline "
                f"({increase_ratio:.0%} change)."
            )
        else:
            confirmed = False
            notes.append("Supplier no longer reports a lead time above its baseline; risk appears resolved.")

    updates: dict = {
        "disruption_type": disruption_type,
        "_confirmed": confirmed,
        "_delay_days": delay_days,
        "status": "in_progress" if confirmed else "resolved",
    }
    updates.update(
        log_step(
            state,
            "Disruption Detection Agent",
            input_summary=f"Classifying signal type={disruption_type} for material={state['material']}",
            output_summary=f"confirmed={confirmed}; " + " ".join(notes),
            evidence={"delay_days": delay_days, "notes": notes},
        )
    )
    return updates
