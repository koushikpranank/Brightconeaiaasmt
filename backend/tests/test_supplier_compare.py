"""Unit tests for supplier scoring - specifically that capacity is evaluated as its own
dimension (Requirement 6), separate from current on-hand available_quantity."""
from app.tools.supplier_compare import rank_suppliers, score_supplier


def test_full_data_including_capacity_is_confirmed():
    score = score_supplier(
        supplier_code="SUP-100",
        name="Reliable Metals",
        lead_time_days=7,
        price_per_unit=850,
        available_quantity=120,
        capacity_units_per_month=300,
        approved=True,
        required_quantity=100,
    )
    assert score.data_confidence == "confirmed"
    assert score.meets_quantity is True
    assert score.meets_capacity is True


def test_missing_capacity_alone_requires_verification():
    """Even with everything else known, a missing capacity figure is enough to withhold
    "confirmed" - capacity is not inferred from available_quantity."""
    score = score_supplier(
        supplier_code="SUP-101",
        name="Unknown Capacity Co",
        lead_time_days=7,
        price_per_unit=850,
        available_quantity=120,
        capacity_units_per_month=None,
        approved=True,
        required_quantity=100,
    )
    assert score.data_confidence == "requires_verification"
    assert score.meets_quantity is True
    assert score.meets_capacity is None  # unknown, not assumed


def test_capacity_below_requirement_is_flagged_not_hidden():
    """A supplier can have stock on the shelf today but not enough ongoing capacity to
    keep the plant supplied - that must surface as meets_capacity=False, not be dropped."""
    score = score_supplier(
        supplier_code="SUP-102",
        name="Small Batch Supplier",
        lead_time_days=5,
        price_per_unit=900,
        available_quantity=150,
        capacity_units_per_month=40,
        approved=True,
        required_quantity=100,
    )
    assert score.data_confidence == "confirmed"  # all four fields are known
    assert score.meets_quantity is True  # has enough on hand right now
    assert score.meets_capacity is False  # but can't keep up with demand long-term


def test_rank_suppliers_orders_confirmed_first_by_lead_time_and_price():
    # rank_score = lead_time_days + 0.1 * price_per_unit (lower wins):
    # SUP-A -> 20 + 0.1*100 = 30 ; SUP-B -> 5 + 0.1*110 = 16
    scores = [
        score_supplier("SUP-A", "Slow & Cheap", 20, 100, 100, capacity_units_per_month=200, approved=True),
        score_supplier("SUP-B", "Fast & Similar Price", 5, 110, 100, capacity_units_per_month=200, approved=True),
        score_supplier("SUP-C", "Unverified", None, None, None, capacity_units_per_month=None, approved=True),
    ]
    ranked = rank_suppliers(scores)
    assert ranked[0].supplier_code == "SUP-B"  # lowest combined lead-time + price score
    assert ranked[-1].supplier_code == "SUP-C"  # unconfirmed suppliers always sort last
