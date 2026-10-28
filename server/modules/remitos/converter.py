import re
from dataclasses import dataclass

from server.modules.catalog.models import ProductType


@dataclass
class PackageParseResult:
    """Result of parsing a supplier description for packaging information."""

    package_type: str  # "caja", "pack", "bolsa", "display", "unidad", "kg", "grams"
    multiplier: int  # Sellable units per package (or grams for bulk)
    target_unit_type: str  # "discrete_unit" or "bulk_grams"
    inner_weight_grams: int | None  # Weight per inner unit if detected
    confidence: int  # 0-100


# Ordered by specificity — first match wins
MULTIPLIER_PATTERNS: list[tuple[str, str, bool]] = [
    # (regex_pattern, package_type_name, is_weight_indicator)
    (r"[x×]\s*(\d+)\s*(?:u(?:n(?:idades?)?)?\.?)\b", "caja", False),
    (r"pack\s*(?:de|x)?\s*(\d+)", "pack", False),
    (r"display\s*(?:de|x)?\s*(\d+)", "display", False),
    (r"caja\s*(?:de|x)?\s*(\d+)", "caja", False),
    (
        r"(?:bolsa|bolson)\s*(?:de|x)?\s*(\d+(?:[.,]\d+)?)\s*(?:kg|kilos?)?",
        "bolsa",
        True,
    ),
    (r"[x×]\s*(\d+(?:[.,]\d+)?)\s*(?:kg|kilos?)\b", "kg", True),
    (r"[x×]\s*(?:kg|kilos?)\b", "kg", True),
    (r"[x×]\s*(\d+[.,]\d+)\b", "kg", True),
    (r"[x×]\s*(\d+)\s*(?:gr?(?:s|amos?)?)\b", "grams", True),
]

# Inner unit weight detection (e.g. "x 41 gr" in "Barritas x 41 gr x 10 u")
INNER_WEIGHT_PATTERN = re.compile(
    r"\b(\d+)\s*(?:gr?(?:amos?|s)?|cc|ml)\b", re.IGNORECASE
)


def parse_packaging(
    raw_description: str,
    product_type: ProductType | None = None,
) -> PackageParseResult:
    """Extract packaging multiplier and type from raw supplier item description."""
    text = raw_description.lower().strip()
    is_bulk = product_type == ProductType.BULK

    # Detect inner individual unit weight if present
    inner_wt = None
    wt_match = INNER_WEIGHT_PATTERN.search(text)
    if wt_match:
        inner_wt = int(wt_match.group(1))

    for pattern, pkg_type, is_weight in MULTIPLIER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Standalone "x kg" has no capture group
            if match.groups() and match.group(1):
                val = float(match.group(1).replace(",", "."))
            else:
                val = 1.0

            if is_weight:
                mult = int(val) if pkg_type == "grams" else int(val * 1000)
                target = "bulk_grams" if (is_bulk or mult >= 1000) else "discrete_unit"
                multiplier = mult if target == "bulk_grams" else 1
                inner = inner_wt if target == "discrete_unit" else None
                return PackageParseResult(pkg_type, multiplier, target, inner, 85)

            return PackageParseResult(pkg_type, int(val), "discrete_unit", inner_wt, 90)

    # Fallback to single discrete unit or bulk default
    target = "bulk_grams" if is_bulk else "discrete_unit"
    return PackageParseResult("unidad", 1, target, inner_wt, 50)
