import pytest

from server.modules.remitos.fiscal import compute_unit_cost


def test_fiscal_standard_60_40_split():
    # 1 Caja Barritas x 10 u @ $5,000 / caja, 60% blanco, 40% negro, 21% IVA
    res = compute_unit_cost(
        pack_price=5000,
        multiplier=10,
        blanco_bps=6000,
        negro_bps=4000,
        iva_rate_bps=2100,
    )
    assert res.effective_factor_bps == 11260
    assert res.real_pack_cost == 5630
    assert res.real_unit_cost == 563


def test_fiscal_bulk_reference_weight():
    # 1 Bolsa Almendras x 10 kg (10,000g) @ $45,000, 60/40, 21% IVA
    res = compute_unit_cost(
        pack_price=45000,
        multiplier=10000,
        blanco_bps=6000,
        negro_bps=4000,
        iva_rate_bps=2100,
        is_bulk=True,
        bulk_reference_grams=100,
    )
    assert res.real_pack_cost == 50670
    assert res.real_unit_cost == 507  # $507 per 100g


def test_fiscal_pure_negro():
    # 0% blanco, 100% negro -> Factor = 1.000
    res = compute_unit_cost(
        pack_price=8000,
        multiplier=20,
        blanco_bps=0,
        negro_bps=10000,
        iva_rate_bps=2100,
    )
    assert res.effective_factor_bps == 10000
    assert res.real_pack_cost == 8000
    assert res.real_unit_cost == 400
    assert res.iva_amount_per_pack == 0


def test_fiscal_pure_blanco():
    # 100% blanco, 0% negro, 21% IVA -> Factor = 1.210
    res = compute_unit_cost(
        pack_price=6000,
        multiplier=12,
        blanco_bps=10000,
        negro_bps=0,
        iva_rate_bps=2100,
    )
    assert res.effective_factor_bps == 12100
    assert res.real_pack_cost == 7260
    assert res.real_unit_cost == 605


def test_fiscal_with_discount():
    # 10% global discount on $10,000 pack @ 60/40
    res = compute_unit_cost(
        pack_price=10000,
        multiplier=1,
        blanco_bps=6000,
        negro_bps=4000,
        iva_rate_bps=2100,
        discount_pct=10,
    )
    # 10000 * 1.126 = 11260; with 10% off -> 10134
    assert res.real_pack_cost == 10134


def test_fiscal_invalid_multiplier():
    with pytest.raises(ValueError, match="Multiplier must be positive"):
        compute_unit_cost(pack_price=1000, multiplier=0)
