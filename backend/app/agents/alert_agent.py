"""Agent 6 - Alert & Response Planning Agent.

Consolidates everything the earlier agents found into one alert, deduplicates against
already-open alerts for the same (material, disruption_type, source) instead of spamming
a new one on every monitoring pass, assigns action items to responsible teams, and sends
the notification (log-mode by default, see app.integrations.email_api).
"""
from sqlmodel import Session, select

from app.agents.state import CaseState, log_step
from app.integrations.email_api import send_alert_email
from app.llm import explain
from app.models import ActionItem, Alert
from app.tools.inventory_math import build_dedup_key

TEAM_BY_DISRUPTION_TYPE = {
    "supplier_delay": "Procurement",
    "shipment_delay": "Logistics",
    "shortage": "Inventory Planning",
    "low_inventory": "Inventory Planning",
    "supplier_unavailable": "Procurement",
    "lead_time_increase": "Procurement",
}


def node(state: CaseState, session: Session, case_db_id: int) -> dict:
    material = state["material"]
    disruption_type = state["disruption_type"]
    source = state.get("source", "unknown")
    impact = state.get("impact", {})
    mitigation = state.get("mitigation", {})

    dedup_key = build_dedup_key(material, disruption_type, source)
    responsible_team = TEAM_BY_DISRUPTION_TYPE.get(disruption_type, "Supply Chain Management")

    expected_impact = impact.get("summary", "Impact assessment pending.")
    recommended_action = mitigation.get("recommended_actions", ["Review manually."])[0]

    existing = session.exec(select(Alert).where(Alert.dedup_key == dedup_key)).first()
    if existing:
        existing.expected_impact = expected_impact
        existing.recommended_action = recommended_action
        existing.status = "updated"
        existing.occurrence_count += 1
        session.add(existing)
        session.commit()
        session.refresh(existing)
        alert_row = existing
    else:
        alert_row = Alert(
            dedup_key=dedup_key,
            case_id=case_db_id,
            disruption_type=disruption_type,
            material=material,
            source=source,
            expected_impact=expected_impact,
            recommended_action=recommended_action,
            responsible_team=responsible_team,
            status="open",
        )
        session.add(alert_row)
        session.commit()
        session.refresh(alert_row)

    for action_text in mitigation.get("recommended_actions", []):
        session.add(
            ActionItem(
                case_id=case_db_id,
                description=action_text,
                responsible_team=responsible_team,
            )
        )
    session.commit()

    subject = f"[Disruption Alert] {disruption_type.replace('_', ' ').title()} - {material}"
    body = explain(
        "Draft a concise alert notification body for the supply chain manager covering disruption type, "
        "affected material, source, expected impact, and recommended action.",
        {
            "disruption_type": disruption_type,
            "material": material,
            "source": source,
            "expected_impact": expected_impact,
            "recommended_action": recommended_action,
            "responsible_team": responsible_team,
        },
    )
    notification_result = send_alert_email(subject, body)

    alert_payload = {
        "id": alert_row.id,
        "dedup_key": dedup_key,
        "disruption_type": disruption_type,
        "material": material,
        "source": source,
        "expected_impact": expected_impact,
        "recommended_action": recommended_action,
        "responsible_team": responsible_team,
        "status": alert_row.status,
    }

    updates = {"alert": alert_payload}
    updates.update(
        log_step(
            state,
            "Alert & Response Planning Agent",
            input_summary=f"Consolidating findings for {material}/{disruption_type}",
            output_summary=f"Alert {'updated' if existing else 'created'} ({dedup_key}); notification={notification_result['mode']}",
            evidence={"alert": alert_payload, "notification": notification_result},
        )
    )
    return updates
