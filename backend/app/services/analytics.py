"""Historical analytics over disruption history, built with pandas.

This is deliberately separate from the deterministic per-case math in `app.tools` (which
must never depend on anything beyond plain Python): those functions answer "what is true
about this one case right now", while this module answers "what does the pattern look like
across every case we've ever seen" - aggregation is exactly what pandas is for, and doing
it by hand in a loop would just be a worse pandas.
"""
from datetime import datetime, timedelta

import pandas as pd
from sqlmodel import Session, select

from app.models import Alert, DisruptionCase, DisruptionEventRecord


def _cases_frame(session: Session) -> pd.DataFrame:
    cases = session.exec(select(DisruptionCase)).all()
    events_by_id = {e.id: e for e in session.exec(select(DisruptionEventRecord)).all()}

    rows = []
    for case in cases:
        event = events_by_id.get(case.event_id)
        impact = case.impact or {}
        rows.append(
            {
                "case_number": case.case_number,
                "status": case.status,
                "material": event.material if event else None,
                "disruption_type": event.disruption_type if event else None,
                "severity": impact.get("severity", "unknown"),
                "mitigation_window_days": impact.get("mitigation_window_days"),
                "revision_count": case.revision_count,
                "created_at": case.created_at,
                "updated_at": case.updated_at,
            }
        )
    columns = [
        "case_number", "status", "material", "disruption_type", "severity",
        "mitigation_window_days", "revision_count", "created_at", "updated_at",
    ]
    return pd.DataFrame(rows, columns=columns)


def _alerts_frame(session: Session) -> pd.DataFrame:
    alerts = session.exec(select(Alert)).all()
    rows = [
        {
            "material": a.material,
            "disruption_type": a.disruption_type,
            "responsible_team": a.responsible_team,
            "status": a.status,
            "occurrence_count": a.occurrence_count,
            "created_at": a.created_at,
        }
        for a in alerts
    ]
    return pd.DataFrame(rows, columns=["material", "disruption_type", "responsible_team", "status", "occurrence_count", "created_at"])


def disruption_frequency_by_material(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    counts = df.groupby("material").size().sort_values(ascending=False)
    return [{"material": material, "count": int(count)} for material, count in counts.items()]


def severity_distribution(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    counts = df["severity"].fillna("unknown").value_counts()
    return [{"severity": severity, "count": int(count)} for severity, count in counts.items()]


def disruption_type_breakdown(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    counts = df["disruption_type"].fillna("unknown").value_counts()
    return [{"disruption_type": dtype, "count": int(count)} for dtype, count in counts.items()]


def avg_mitigation_window_by_severity(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    numeric = df.dropna(subset=["mitigation_window_days"])
    if numeric.empty:
        return []
    grouped = numeric.groupby("severity")["mitigation_window_days"].mean().round(1)
    return [{"severity": severity, "avg_mitigation_window_days": float(value)} for severity, value in grouped.items()]


def alerts_by_team(alerts_df: pd.DataFrame) -> list[dict]:
    if alerts_df.empty:
        return []
    grouped = alerts_df.groupby("responsible_team").agg(
        total_alerts=("occurrence_count", "sum"),
        open_alerts=("status", lambda s: int((s == "open").sum() + (s == "updated").sum())),
    )
    return [
        {"team": team, "total_alerts": int(row.total_alerts), "open_alerts": int(row.open_alerts)}
        for team, row in grouped.iterrows()
    ]


def cases_per_day(df: pd.DataFrame, days: int = 14) -> list[dict]:
    if df.empty:
        return []
    since = datetime.utcnow() - timedelta(days=days)
    recent = df[df["created_at"] >= since].copy()
    if recent.empty:
        return []
    recent["day"] = recent["created_at"].dt.strftime("%Y-%m-%d")
    counts = recent.groupby("day").size()
    return [{"date": day, "count": int(count)} for day, count in counts.items()]


def revision_rate(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"total_cases": 0, "cases_revised": 0, "revision_rate_pct": 0.0}
    total = len(df)
    revised = int((df["revision_count"] > 0).sum())
    return {
        "total_cases": total,
        "cases_revised": revised,
        "revision_rate_pct": round(100 * revised / total, 1) if total else 0.0,
    }


def build_summary(session: Session) -> dict:
    cases_df = _cases_frame(session)
    alerts_df = _alerts_frame(session)

    return {
        "disruption_frequency_by_material": disruption_frequency_by_material(cases_df),
        "severity_distribution": severity_distribution(cases_df),
        "disruption_type_breakdown": disruption_type_breakdown(cases_df),
        "avg_mitigation_window_by_severity": avg_mitigation_window_by_severity(cases_df),
        "alerts_by_team": alerts_by_team(alerts_df),
        "cases_per_day": cases_per_day(cases_df),
        "reviewer_revision_rate": revision_rate(cases_df),
        "total_cases": int(len(cases_df)),
        "total_alerts": int(len(alerts_df)),
    }
