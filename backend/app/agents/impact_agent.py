"""Agent 4 - Impact Assessment Agent."""
from datetime import date

from sqlmodel import Session, select

from app.agents.state import CaseState, log_step
from app.llm import explain
from app.models import ProductionOrder, PurchaseOrder
from app.tools.inventory_math import calculate_mitigation_window, classify_severity


def node(state: CaseState, session: Session) -> dict:
    material = state["material"]
    inventory_analysis = state.get("inventory_analysis", {})

    affected_pos = session.exec(
        select(PurchaseOrder).where(PurchaseOrder.material == material, PurchaseOrder.status != "fulfilled")
    ).all()
    affected_production = session.exec(
        select(ProductionOrder).where(ProductionOrder.material == material, ProductionOrder.status != "completed")
    ).all()

    projected_stockout = inventory_analysis.get("projected_stockout_date")
    stockout_date = date.fromisoformat(projected_stockout) if projected_stockout else None
    mitigation_window = calculate_mitigation_window(stockout_date, date.today())
    severity = classify_severity(mitigation_window, inventory_analysis.get("coverage_days"))

    impact = {
        "affected_purchase_orders": [po.po_number for po in affected_pos],
        "affected_production_orders": [po.order_number for po in affected_production],
        "affected_customers": sorted({po.customer for po in affected_production}),
        "estimated_delay_days": state.get("_delay_days", 0),
        "mitigation_window_days": mitigation_window,
        "severity": severity,
    }

    narration = explain(
        "Summarize the operational impact of this disruption for a supply chain manager.",
        {
            "material": material,
            "affected_production_orders": len(impact["affected_production_orders"]),
            "affected_customers": len(impact["affected_customers"]),
            "severity": severity,
            "mitigation_window_days": mitigation_window,
        },
    )
    impact["summary"] = narration

    updates = {"impact": impact}
    updates.update(
        log_step(
            state,
            "Impact Assessment Agent",
            input_summary=f"Cross-referencing open POs/production orders for {material}",
            output_summary=narration,
            evidence=impact,
        )
    )
    return updates
