"""EAN-13 / In-Store Embedded Weight Barcode Parser for label printing scales."""

from pydantic import BaseModel

IN_STORE_PREFIXES: set[str] = {"20", "21", "28", "29"}


class ParsedBarcode(BaseModel):
    """Result of parsing an in-store or retail barcode."""

    raw_barcode: str
    is_embedded_weight: bool
    sku_or_plu: str
    weight_grams: int | None = None


def parse_barcode(raw: str) -> ParsedBarcode:
    """Parse raw barcode string into discrete SKU or scale-embedded PLU & weight.

    Scale labels in dietetic stores follow GS1 In-Store EAN embedded format:
      PP IIII WWWWW C (12 or 13 digits)
      - PP: In-store prefix (20, 21, 28, 29)
      - IIII: 4-digit PLU code (or 4/5 digits)
      - WWWWW: 5-digit weight in grams
      - C: Check digit
    """
    clean = raw.strip()

    if len(clean) in (12, 13) and clean.isdigit():
        prefix = clean[:2]
        if prefix in IN_STORE_PREFIXES:
            plu = clean[2:6]
            weight_grams = int(clean[6:11])
            return ParsedBarcode(
                raw_barcode=clean,
                is_embedded_weight=True,
                sku_or_plu=plu,
                weight_grams=weight_grams,
            )

    return ParsedBarcode(
        raw_barcode=clean,
        is_embedded_weight=False,
        sku_or_plu=clean,
        weight_grams=None,
    )
