import difflib
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from server.modules.catalog.models import Product, ProductType
from server.modules.remitos.converter import parse_packaging
from server.modules.remitos.models import (
    MatchStrategy,
    SupplierProductMapping,
    TargetUnitType,
)
from server.modules.remitos.text import (
    normalize_supplier_text,
    strip_packaging_noise,
)

__all__ = [
    "match_supplier_item",
    "normalize_supplier_text",
    "strip_packaging_noise",
    "tier1_exact_alias",
    "tier2_fuzzy_match",
    "upsert_alias_mapping",
]


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
    if alias := await tier1_exact_alias(db, supplier_name, raw_description):
        return (
            alias.product_id,
            100,
            MatchStrategy.EXACT_ALIAS,
            alias.multiplier,
            alias.package_type,
            alias.target_unit_type,
        )

    pkg = parse_packaging(raw_description, product_type=product_type)
    is_bulk = pkg.target_unit_type == "bulk_grams"
    target_type = TargetUnitType.BULK_GRAMS if is_bulk else TargetUnitType.DISCRETE_UNIT

    fuzzy_matches = await tier2_fuzzy_match(db, raw_description, limit=1)
    res = (pkg.multiplier, pkg.package_type, target_type)
    if fuzzy_matches and fuzzy_matches[0][1] >= 65:
        return (
            fuzzy_matches[0][0].id,
            fuzzy_matches[0][1],
            MatchStrategy.FUZZY_CATALOG,
            *res,
        )
    return (None, 0, MatchStrategy.UNMATCHED, *res)


async def upsert_alias_mapping(
    db: AsyncSession,
    supplier_name: str,
    raw_description: str,
    product_id: int,
    multiplier: int,
    package_type: str | None,
    target_unit_type: TargetUnitType,
) -> None:
    """Upsert alias dictionary mapping for verified items."""
    norm = normalize_supplier_text(raw_description)
    stmt = select(SupplierProductMapping).where(
        col(SupplierProductMapping.supplier_name).ilike(supplier_name),
        SupplierProductMapping.raw_item_pattern == norm,
    )
    existing = (await db.scalars(stmt)).first()
    if existing:
        existing.product_id, existing.multiplier = product_id, multiplier
        existing.package_type = package_type
        existing.target_unit_type = target_unit_type
        existing.times_used += 1
        existing.last_matched_at = datetime.now(timezone.utc)
    else:
        db.add(
            SupplierProductMapping(
                supplier_name=supplier_name,
                raw_item_pattern=norm,
                product_id=product_id,
                package_type=package_type,
                multiplier=multiplier,
                target_unit_type=target_unit_type,
            )
        )
