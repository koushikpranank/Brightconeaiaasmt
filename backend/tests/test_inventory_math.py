from datetime import date, datetime

from app.tools.inventory_math import (
    build_dedup_key,
    calculate_delay_impact,
    calculate_inventory_coverage,
    calculate_mitigation_window,
    classify_severity,
)


def test_steel_plate_coverage_matches_spec_example():
    result = calculate_inventory_coverage(
        current_quantity=25,
        daily_consumption=5,
        snapshot_at=datetime(2026, 9, 19, 8, 0, 0),
        reorder_point_days=10,
        revised_delivery_date=date(2026, 9, 30),
    )
    assert result.coverage_days == 5.0
    assert result.projected_stockout_date == date(2026, 9, 24)
    assert result.stockout_calculable is True
    assert result.reorder_required is True
    assert any("precedes the revised delivery date" in n for n in result.notes)


def test_stockout_date_not_invented_without_snapshot():
    result = calculate_inventory_coverage(
        current_quantity=25,
        daily_consumption=5,
        snapshot_at=None,
        reorder_point_days=10,
    )
    assert result.projected_stockout_date is None
    assert result.stockout_calculable is False
    assert any("cannot be derived" in n for n in result.notes)


def test_delay_impact_days():
    assert calculate_delay_impact(date(2026, 9, 20), date(2026, 9, 30)) == 10
    assert calculate_delay_impact(date(2026, 9, 20), date(2026, 9, 15)) == 0


def test_mitigation_window_and_severity():
    window = calculate_mitigation_window(date(2026, 9, 24), date(2026, 9, 19))
    assert window == 5
    assert classify_severity(window, 5.0) == "medium"
    assert classify_severity(-2, 1.0) == "critical"
    assert classify_severity(None, None) == "unknown"


def test_dedup_key_is_stable_and_case_insensitive():
    a = build_dedup_key("Steel Plate", "supplier_delay", "po:PO-1001")
    b = build_dedup_key("steel plate", "supplier_delay", "po:PO-1001")
    assert a == b
