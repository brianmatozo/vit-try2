import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.modules.catalog.models import Product, ProductType
from server.modules.remitos.matching import (
    normalize_supplier_text,
    strip_packaging_noise,
    tier2_fuzzy_match,
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
