from server.modules.remitos.audit import validate_line_totals
from server.modules.remitos.schemas import ExtractedLineItem


def test_validate_line_totals_exact_match():
    items = [
        ExtractedLineItem(
            line_index=0,
            raw_description="Item 1",
            quantity=2,
            unit_cost=5000,
            line_total=10000,
        ),
        ExtractedLineItem(
            line_index=1,
            raw_description="Item 2",
            quantity=1,
            unit_cost=15000,
            line_total=15000,
        ),
    ]
    is_valid, discrepancy = validate_line_totals(items, 25000)
    assert is_valid is True
    assert discrepancy == 0


def test_validate_line_totals_within_tolerance():
    items = [
        ExtractedLineItem(
            line_index=0,
            raw_description="Item 1",
            quantity=1,
            unit_cost=9950,
            line_total=9950,
        ),
    ]
    # Total 10000 -> 1% threshold is 100 ARS. Discrepancy is 50 ARS <= 100.
    is_valid, discrepancy = validate_line_totals(items, 10000)
    assert is_valid is True
    assert discrepancy == 50


def test_validate_line_totals_exceeds_tolerance():
    items = [
        ExtractedLineItem(
            line_index=0,
            raw_description="Item 1",
            quantity=1,
            unit_cost=9500,
            line_total=9500,
        ),
    ]
    # Total 10000 -> 1% threshold is 100 ARS. Discrepancy is 500 ARS > 100.
    is_valid, discrepancy = validate_line_totals(items, 10000)
    assert is_valid is False
    assert discrepancy == 500


def test_validate_line_totals_none_or_zero_total():
    items = [
        ExtractedLineItem(
            line_index=0,
            raw_description="Item 1",
            quantity=1,
            unit_cost=5000,
            line_total=5000,
        ),
    ]
    is_valid_none, disc_none = validate_line_totals(items, None)
    assert is_valid_none is True
    assert disc_none == 0

    is_valid_zero, disc_zero = validate_line_totals(items, 0)
    assert is_valid_zero is True
    assert disc_zero == 0
