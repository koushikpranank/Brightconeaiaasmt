"""Agent 5 - Alternative Supplier & Mitigation Agent.

Never invents a supplier, quote, or lead time: every option comes straight from
`app.integrations.supplier_api` (the simulated supplier data source). Suppliers with
incomplete data are surfaced with data_confidence="requires_verification" rather than
silently dropped or guessed at.
"""
from sqlmodel import Session, select

from app.agents.state import CaseState, log_step
from app.integrations import inventory_api, supplier_api
from app.llm import explain
from app.models import InventoryItem
from app.tools.supplier_compare import rank_suppliers, score_supplier


def node(state: CaseState, session: Session) -> dict:
    material = state["material"]
    excluded_supplier = state.get("_supplier_code")

    required_quantity = None
    inventory_item = session.exec(select(InventoryItem).where(InventoryItem.material == material)).first()
    if inventory_item:
        required_quantity = inventory_item.required_quantity

    alternatives = supplier_api.list_approved_suppliers(session, material, exclude_supplier_code=excluded_supplier)

    scores = [
        score_supplier(
            supplier_code=alt["supplier_code"],
            name=alt["name"],
            lead_time_days=alt["lead_time_days"],
            price_per_unit=alt["price_per_unit"],
            available_quantity=alt["available_quantity"],
            capacity_units_per_month=alt.get("capacity_units_per_month"),
            approved=alt["approved"],
            required_quantity=required_quantity,
        )
        for alt in alternatives
    ]
    ranked = rank_suppliers(scores)

    options = [
        {
            "supplier_code": s.supplier_code,
            "name": s.name,
            "lead_time_days": s.lead_time_days,
            "price_per_unit": s.price_per_unit,
            "available_quantity": s.available_quantity,
            "capacity_units_per_month": s.capacity_units_per_month,
            "meets_required_quantity": s.meets_quantity,
            "meets_capacity": s.meets_capacity,
            "approved": s.approved,
            "data_confidence": s.data_confidence,
        }
        for s in ranked
    ]

    verification_needed = [o["supplier_code"] for o in options if o["data_confidence"] == "requires_verification"]

    if options:
        best = options[0]
        headline_action = (
            f"Evaluate {best['name']} ({best['supplier_code']}) as an alternate source"
            + (" - confirmed available." if best["data_confidence"] == "confirmed" else " - data requires verification before use.")
        )
    else:
        headline_action = "No approved alternative supplier is on file for this material; escalate for sourcing."

    recommended_actions = [
        headline_action,
        "Contact the existing supplier to request expedited delivery or a firm revised date in writing.",
        "Review production priorities for orders consuming this material.",
        "Evaluate additional procurement cost against the mitigation window before committing.",
    ]

    mitigation = {
        "options": options,
        "recommended_actions": recommended_actions,
        "headline_action": headline_action,
        "requires_human_approval": True,
        "verification_needed": verification_needed,
        "required_quantity": required_quantity,
    }

    narration = explain(
        "Summarize the mitigation options available for this material shortage.",
        {
            "material": material,
            "num_alternatives": len(options),
            "best_option": options[0]["name"] if options else None,
            "verification_needed": len(verification_needed),
        },
    )
    mitigation["narrative"] = narration

    updates = {"mitigation": mitigation, "supplier_options": options}
    updates.update(
        log_step(
            state,
            "Alternative Supplier & Mitigation Agent",
            input_summary=f"Comparing approved alternative suppliers for {material}",
            output_summary=narration,
            evidence=mitigation,
        )
    )
    return updates
