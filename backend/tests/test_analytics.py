"""Tests for the pandas-powered analytics aggregations."""
from datetime import datetime

from sqlmodel import Session, select

from app.integrations.supplier_api import announce_delay
from app.models import AgentDecisionLog, DisruptionCase, InventoryItem, ProductionOrder, Supplier
from app.services.analytics import build_summary
from app.services.case_runner import run_monitoring_sweep


def test_analytics_summary_on_empty_database(session: Session):
    summary = build_summary(session)
    assert summary["total_cases"] == 0
    assert summary["total_alerts"] == 0
    assert summary["disruption_frequency_by_material"] == []
    assert summary["severity_distribution"] == []
    assert summary["reviewer_revision_rate"] == {"total_cases": 0, "cases_revised": 0, "revision_rate_pct": 0.0}


def test_analytics_summary_reflects_real_cases(steel_plate_scenario: Session):
    session = steel_plate_scenario
    announce_delay(session, "PO-1001", 10, "supplier announced a 10-day delay")
    run_monitoring_sweep(session)

    summary = build_summary(session)

    assert summary["total_cases"] == 1
    assert summary["total_alerts"] == 1
    assert {"material": "Steel Plate", "count": 1} in summary["disruption_frequency_by_material"]
    assert any(row["disruption_type"] == "supplier_delay" for row in summary["disruption_type_breakdown"])
    assert any(row["team"] == "Procurement" for row in summary["alerts_by_team"])
    # severity was calculable (a snapshot date exists), so it must not be silently omitted
    severities = {row["severity"] for row in summary["severity_distribution"]}
    assert "unknown" not in severities or len(severities) > 1


def test_case_trace_is_ordered_and_covers_every_agent(steel_plate_scenario: Session):
    """The explainability trace (Context Lake) must show every agent's step, in the order
    they actually ran, each with its own evidence - not a summary that hides the chain."""
    session = steel_plate_scenario
    announce_delay(session, "PO-1001", 10, "supplier announced a 10-day delay")
    run_monitoring_sweep(session)

    case = session.exec(select(DisruptionCase)).first()
    entries = session.exec(
        select(AgentDecisionLog).where(AgentDecisionLog.case_id == case.id).order_by(AgentDecisionLog.created_at.asc())
    ).all()

    agent_names = [e.agent_name for e in entries]
    assert "Supply Chain Monitoring Agent" in agent_names
    assert "Disruption Detection Agent" in agent_names
    assert "Inventory & Demand Analysis Agent" in agent_names
    assert "Impact Assessment Agent" in agent_names
    assert "Alternative Supplier & Mitigation Agent" in agent_names
    assert "Alert & Response Planning Agent" in agent_names
    assert "Reviewer / Critic Agent" in agent_names
    # Monitoring must come before Detection, which must come before the Reviewer's audit.
    assert agent_names.index("Supply Chain Monitoring Agent") < agent_names.index("Disruption Detection Agent")
    assert agent_names.index("Disruption Detection Agent") < agent_names.index("Reviewer / Critic Agent")
    # Every entry carries real evidence, not an empty placeholder.
    assert all(e.evidence for e in entries)
