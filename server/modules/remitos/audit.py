from typing import Any


def validate_line_totals(
    items: list[Any],
    fiscal_total: int | None,
) -> tuple[bool, int]:
    """Check if sum of extracted line totals matches document total.

    Args:
        items: List of line items (with extracted_line_total or line_total).
        fiscal_total: Document total printed on delivery note in whole ARS.

    Returns:
        (is_valid, discrepancy_ars) where is_valid is True if discrepancy <= 1%.
    """
    computed_sum = 0
    for it in items:
        if hasattr(it, "extracted_line_total") and it.extracted_line_total is not None:
            computed_sum += it.extracted_line_total
        elif hasattr(it, "line_total") and it.line_total is not None:
            computed_sum += it.line_total

    if fiscal_total is None or fiscal_total == 0:
        return True, 0

    discrepancy = abs(computed_sum - fiscal_total)
    threshold = max(fiscal_total // 100, 1)
    return discrepancy <= threshold, discrepancy
