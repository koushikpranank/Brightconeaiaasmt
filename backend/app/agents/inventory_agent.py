"""Agent 3 - Inventory & Demand Analysis Agent.

All numbers here come from `app.tools.inventory_math`, deterministic functions - this
agent's job is to fetch the right inputs and hand them to those functions, and to phrase
the result, never to compute a number itself.
"""
from datetime import date, datetime

from sqlmodel import Session

from app.agents.state import CaseState, log_step
from app.integrations import inventory_api
from app.llm import explain
from app.tools.inventory_math import calculate_inventory_coverage


def node(state: CaseState, session: Session) -> dict:
    material = state["material"]
    snapshot = inventory_api.get_inventory_snapshot(session, material)

    revised_delivery = state.get("revised_delivery_date")
    revised_date = date.fromisoformat(revised_delivery) if revised_delivery else None

    if not snapshot:
        analysis = {
            "material": material,
            "current_quantity": None,
            "daily_consumption": None,
            "snapshot_at": None,
            "coverage_days": None,
            "projected_stockout_date": None,
            "stockout_calculable": False,
            "reorder_required": False,
            "notes": ["No inventory record found for this material."],
        }
    else:
        snapshot_at = datetime.fromisoformat(snapshot["snapshot_at"]) if snapshot["snapshot_at"] else None
        result = calculate_inventory_coverage(
            current_quantity=snapshot["current_quantity"],
            daily_consumption=snapshot["daily_consumption"],
            snapshot_at=snapshot_at,
            reorder_point_days=snapshot["reorder_point_days"],
            revised_delivery_date=revised_date,
        )
        analysis = {
            "material": material,
            "current_quantity": snapshot["current_quantity"],
            "daily_consumption": snapshot["daily_consumption"],
            "snapshot_at": snapshot["snapshot_at"],
            "coverage_days": result.coverage_days,
            "projected_stockout_date": result.projected_stockout_date.isoformat() if result.projected_stockout_date else None,
            "stockout_calculable": result.stockout_calculable,
            "reorder_required": result.reorder_required,
            "notes": result.notes,
        }

    narration = explain(
        "Summarize the inventory coverage situation for the supply chain manager in one sentence.",
        {
            "material": material,
            "coverage_days": analysis["coverage_days"],
            "projected_stockout_date": analysis["projected_stockout_date"],
            "reorder_required": analysis["reorder_required"],
        },
    )
    analysis["narrative"] = narration

    updates = {"inventory_analysis": analysis}
    updates.update(
        log_step(
            state,
            "Inventory & Demand Analysis Agent",
            input_summary=f"Inventory snapshot lookup for {material}",
            output_summary=narration,
            evidence=analysis,
        )
    )
    return updates
