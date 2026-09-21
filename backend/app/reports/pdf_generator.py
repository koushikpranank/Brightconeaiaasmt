"""Generates the Disruption Assessment Report (Requirement 12) as a PDF, built entirely
from the case's persisted fields - no new claims are introduced at report time."""
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Alert, ApprovalRequest, DisruptionCase, DisruptionEventRecord


def build_case_report_pdf(case: DisruptionCase, event: DisruptionEventRecord, alert: Alert | None, approval: ApprovalRequest | None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Disruption Assessment Report", styles["Title"]))
    story.append(Paragraph(f"Case {case.case_number}", styles["Heading3"]))
    story.append(Spacer(1, 12))

    def section(title: str, body: str):
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(Paragraph(body or "-", styles["BodyText"]))
        story.append(Spacer(1, 10))

    section(
        "1. Event Summary",
        f"Material: {event.material}<br/>Disruption type: {event.disruption_type}<br/>"
        f"Detected at: {event.detected_at.isoformat()}<br/>Description: {event.description}",
    )
    section("2. Source Information", f"Source: {event.source}<br/>External reference: {event.external_ref}")

    section("3. Affected Materials", event.material)

    inv = case.inventory_analysis or {}
    section(
        "4. Inventory Analysis",
        f"Current quantity: {inv.get('current_quantity')}<br/>"
        f"Daily consumption: {inv.get('daily_consumption')}<br/>"
        f"Inventory snapshot: {inv.get('snapshot_at') or 'unavailable'}<br/>"
        f"Coverage (days): {inv.get('coverage_days')}<br/>"
        f"Projected stockout date: {inv.get('projected_stockout_date') or 'not calculable (snapshot unavailable)'}<br/>"
        f"Reorder required: {inv.get('reorder_required')}",
    )

    impact = case.impact or {}
    section(
        "5. Estimated Impact",
        f"Severity: {impact.get('severity')}<br/>"
        f"Estimated delay (days): {impact.get('estimated_delay_days')}<br/>"
        f"Mitigation window (days): {impact.get('mitigation_window_days')}<br/>"
        f"Affected purchase orders: {', '.join(impact.get('affected_purchase_orders', [])) or 'none'}<br/>"
        f"Affected production orders: {', '.join(impact.get('affected_production_orders', [])) or 'none'}<br/>"
        f"Affected customers: {', '.join(impact.get('affected_customers', [])) or 'none'}<br/>"
        f"Summary: {impact.get('summary', '')}",
    )

    mitigation = case.mitigation or {}
    story.append(Paragraph("6. Mitigation Options", styles["Heading2"]))
    options = mitigation.get("options", [])
    if options:
        table_data = [["Supplier", "Lead time (d)", "Price/unit", "Available qty", "Capacity/mo", "Confidence"]]
        for o in options:
            table_data.append(
                [
                    o.get("name"),
                    o.get("lead_time_days"),
                    o.get("price_per_unit"),
                    o.get("available_quantity"),
                    o.get("capacity_units_per_month"),
                    o.get("data_confidence"),
                ]
            )
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), "#dddddd"),
                    ("GRID", (0, 0), (-1, -1), 0.5, "#999999"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No confirmed alternative suppliers on file.", styles["BodyText"]))
    story.append(Spacer(1, 10))

    section("7. Recommended Actions", "<br/>".join(f"- {a}" for a in mitigation.get("recommended_actions", [])) or "-")

    approval_text = "No approval requested yet."
    if approval:
        approval_text = (
            f"Action: {approval.action_type}<br/>Status: {approval.status}<br/>"
            f"Decided by: {approval.decided_by or '-'}<br/>Notes: {approval.notes or '-'}"
        )
    section("8. Approval Status", approval_text)

    review = case.review or {}
    section(
        "9. Reviewer Notes",
        f"Approved by reviewer: {review.get('approved')}<br/>Issues raised: {'; '.join(review.get('issues', [])) or 'none'}",
    )

    doc.build(story)
    return buffer.getvalue()
