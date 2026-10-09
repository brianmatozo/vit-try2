"""EAN-13 / In-Store Embedded Scale Barcode Parser for label printing scales."""

from pydantic import BaseModel

IN_STORE_PREFIXES: set[str] = {"20", "21", "28", "29"}


class ParsedBarcode(BaseModel):
    """Result of parsing an in-store or retail barcode."""

    raw_barcode: str
    is_embedded_scale: bool = False
    is_embedded_price: bool = False
    is_embedded_weight: bool = False
    sku_or_plu: str
    embedded_price_whole_ars: int | None = None
    weight_grams: int | None = None


def parse_barcode(raw: str) -> ParsedBarcode:
    """Parse raw barcode string into discrete SKU or scale-embedded PLU & price/weight.

    Scale labels in Argentine dietetic stores follow GS1 In-Store EAN embedded format:
      PP IIII VVVVVV C (13 digits) or PP IIII VVVVV C (12 digits)
      - PP: In-store prefix (20, 21, 28, 29)
      - IIII: 4-digit PLU code
      - VVVVVV: 6-digit payload (Argentine scales encode Total Price in ARS)
      - C: Check digit
    """
    clean = raw.strip()

    if len(clean) in (12, 13) and clean.isdigit():
        prefix = clean[:2]
        if prefix in IN_STORE_PREFIXES:
            plu = clean[2:6]

            if len(clean) == 13:
                price_val = int(clean[6:12])
                return ParsedBarcode(
                    raw_barcode=clean,
                    is_embedded_scale=True,
                    is_embedded_price=True,
                    is_embedded_weight=True,  # Backwards compatibility
                    sku_or_plu=plu,
                    embedded_price_whole_ars=price_val,
                    weight_grams=None,
                )

            # 12-digit format fallback
            val = int(clean[6:11])
            return ParsedBarcode(
                raw_barcode=clean,
                is_embedded_scale=True,
                is_embedded_price=False,
                is_embedded_weight=True,
                sku_or_plu=plu,
                embedded_price_whole_ars=val,
                weight_grams=val,
            )

    return ParsedBarcode(
        raw_barcode=clean,
        is_embedded_scale=False,
        is_embedded_price=False,
        is_embedded_weight=False,
        sku_or_plu=clean,
        embedded_price_whole_ars=None,
        weight_grams=None,
    )
