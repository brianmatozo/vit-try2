import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.modules.catalog.models import Product, ProductType
from server.modules.remitos.matching import (
    match_supplier_item,
    normalize_supplier_text,
    strip_packaging_noise,
    tier1_exact_alias,
    tier2_fuzzy_match,
)
from server.modules.remitos.models import (
    MatchStrategy,
    SupplierProductMapping,
    TargetUnitType,
)


def test_text_normalization():
    raw = "¡PROMO! Barritas de Almendras x 41 gr (Integra) - Oferta"
    norm = normalize_supplier_text(raw)
    assert "promo" not in norm
    assert "oferta" not in norm
    assert "(" not in norm
    assert "barritas de almendras" in norm


def test_strip_packaging_noise():
    raw = "Barritas Almendra x 41 gr x 10 u (Integra)"
    cleaned = strip_packaging_noise(raw)
    assert "x 10 u" not in cleaned
    assert "41 gr" not in cleaned
    assert "almendra" in cleaned


@pytest.mark.anyio
async def test_tier1_exact_alias(async_session: AsyncSession):
    prod = Product(
        sku="BAR-LADDU-MAP",
        name="Barritas Laddu x 12 u",
        unit_price=1000,
        product_type=ProductType.DISCRETE,
    )
    async_session.add(prod)
    await async_session.commit()
    await async_session.refresh(prod)
    assert prod.id is not None

    mapping = SupplierProductMapping(
        supplier_name="New Day",
        raw_item_pattern=normalize_supplier_text("Barritas Laddu x 12 u"),
        product_id=prod.id,
        package_type="caja",
        multiplier=12,
        target_unit_type=TargetUnitType.DISCRETE_UNIT,
    )
    async_session.add(mapping)
    await async_session.commit()

    hit = await tier1_exact_alias(async_session, "New Day", "Barritas Laddu x 12 u")
    assert hit is not None
    assert hit.product_id == prod.id
    assert hit.multiplier == 12
    assert hit.times_used == 2

    miss = await tier1_exact_alias(async_session, "Other", "Barritas Laddu x 12 u")
    assert miss is None


@pytest.mark.anyio
async def test_tier2_fuzzy_matching(async_session: AsyncSession):
    prod = Product(
        sku="ALF-LADDU",
        name="Alfajor Vegano Laddu Chocolate Mascabo",
        unit_price=1500,
        product_type=ProductType.DISCRETE,
    )
    async_session.add(prod)
    await async_session.commit()

    matches = await tier2_fuzzy_match(
        async_session, "Alfajores Laddu Chocolate", limit=1
    )
    assert len(matches) == 1
    assert matches[0][0].id == prod.id
    assert matches[0][1] >= 65


@pytest.mark.anyio
async def test_match_supplier_item_tier_priority(async_session: AsyncSession):
    prod = Product(
        sku="BAR-INTEGRA",
        name="Barrita Integra Almendra",
        unit_price=800,
        product_type=ProductType.DISCRETE,
    )
    async_session.add(prod)
    await async_session.commit()

    # Tier 2 fuzzy hit
    pid, conf, strat, mult, pkg, target = await match_supplier_item(
        async_session, "Distribuidora X", "Barrita Integra Almendra x 10 u"
    )
    assert pid == prod.id
    assert strat == MatchStrategy.FUZZY_CATALOG
    assert mult == 10

    # Tier 1 alias priority
    prod2 = Product(
        sku="BAR-INTEGRA-20",
        name="Barrita Integra Display 20u",
        unit_price=15000,
        product_type=ProductType.DISCRETE,
    )
    async_session.add(prod2)
    await async_session.commit()
    await async_session.refresh(prod2)
    assert prod2.id is not None

    mapping = SupplierProductMapping(
        supplier_name="Distribuidora X",
        raw_item_pattern=normalize_supplier_text("Barrita Integra Almendra x 10 u"),
        product_id=prod2.id,
        package_type="display",
        multiplier=20,
    )
    async_session.add(mapping)
    await async_session.commit()

    pid1, conf1, strat1, mult1, pkg1, _ = await match_supplier_item(
        async_session, "Distribuidora X", "Barrita Integra Almendra x 10 u"
    )
    assert pid1 == prod2.id
    assert strat1 == MatchStrategy.EXACT_ALIAS
    assert mult1 == 20
