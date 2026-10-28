import difflib
import re
import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from server.modules.catalog.models import Product, ProductType
from server.modules.remitos.converter import parse_packaging
from server.modules.remitos.models import (
    MatchStrategy,
    SupplierProductMapping,
    TargetUnitType,
)

PACKAGING_NOISE = re.compile(
    r"\b(?:x\s*\d+\s*(?:u(?:n(?:idades?)?)?\.?|gr?(?:s|amos?)?|kg|kilos?|lt?|ml|cc))"
    r"|\b(?:caja|pack|bolsa|display|promo|oferta|sachet|sobre|unidad)\b"
    r"|\b(?:de|el|la|los|las|por|con|sin)\b"
    r"|[()[\]{}\-–—/\\|.,;:!?\"'`x×¡¿]",
    re.IGNORECASE,
)


def normalize_supplier_text(raw: str) -> str:
    """Normalize supplier text for deterministic alias dictionary lookups."""
    text = unicodedata.normalize("NFKD", raw)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    noise = {"promo", "oferta", "liq", "liquidacion", "desc", "descuento", "nuevo"}
    tokens = [t for t in text.split() if t not in noise]
    return " ".join(tokens)


def strip_packaging_noise(text: str) -> str:
    """Remove packaging markers and noise words for catalog product comparison."""
    cleaned = PACKAGING_NOISE.sub(" ", text)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


async def tier1_exact_alias(
    db: AsyncSession, supplier_name: str, raw_description: str
) -> SupplierProductMapping | None:
    """O(1) cached lookup in supplier_product_mappings dictionary."""
    normalized = normalize_supplier_text(raw_description)
    supplier_norm = supplier_name.strip()
    stmt = select(SupplierProductMapping).where(
        col(SupplierProductMapping.supplier_name).ilike(supplier_norm),
        SupplierProductMapping.raw_item_pattern == normalized,
    )
    mapping = (await db.scalars(stmt)).first()
    if mapping:
        mapping.times_used += 1
    return mapping


async def tier2_fuzzy_match(
    db: AsyncSession, raw_description: str, limit: int = 5
) -> list[tuple[Product, int]]:
    """Fuzzy match against Product.name using SequenceMatcher similarity."""
    cleaned = strip_packaging_noise(raw_description)
    if len(cleaned) < 3:
        return []

    stmt = select(Product).where(Product.is_active == True)  # noqa: E712
    products = (await db.scalars(stmt)).all()

    scored: list[tuple[Product, int]] = []
    for prod in products:
        p_clean = strip_packaging_noise(prod.name)
        score = int(difflib.SequenceMatcher(None, cleaned, p_clean).ratio() * 100)
        if score >= 50:
            scored.append((prod, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


async def match_supplier_item(
    db: AsyncSession,
    supplier_name: str,
    raw_description: str,
    product_type: ProductType | None = None,
) -> tuple[int | None, int, MatchStrategy, int, str | None, TargetUnitType]:
    """Resolve raw item through Tier 1 dictionary and Tier 2 fuzzy matching."""
    # 1. Tier 1: Alias Dictionary
    alias = await tier1_exact_alias(db, supplier_name, raw_description)
    if alias:
        return (
            alias.product_id,
            100,
            MatchStrategy.EXACT_ALIAS,
            alias.multiplier,
            alias.package_type,
            alias.target_unit_type,
        )

    # 2. Extract packaging multiplier
    pkg = parse_packaging(raw_description, product_type=product_type)
    target_type = (
        TargetUnitType.BULK_GRAMS
        if pkg.target_unit_type == "bulk_grams"
        else TargetUnitType.DISCRETE_UNIT
    )

    # 3. Tier 2: Fuzzy Catalog Matching
    fuzzy_matches = await tier2_fuzzy_match(db, raw_description, limit=1)
    if fuzzy_matches and fuzzy_matches[0][1] >= 65:
        top_prod, confidence = fuzzy_matches[0]
        return (
            top_prod.id,
            confidence,
            MatchStrategy.FUZZY_CATALOG,
            pkg.multiplier,
            pkg.package_type,
            target_type,
        )

    # 4. Unmatched fallback
    return (
        None,
        0,
        MatchStrategy.UNMATCHED,
        pkg.multiplier,
        pkg.package_type,
        target_type,
    )
