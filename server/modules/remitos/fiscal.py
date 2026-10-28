from dataclasses import dataclass


@dataclass
class FiscalCostResult:
    """Result of fiscal split cost computation."""

    effective_factor_bps: int  # Cost factor in basis points (e.g. 11260 = 1.126)
    real_pack_cost: int  # Landed package cost (whole ARS)
    real_unit_cost: int  # Cost per sellable unit (whole ARS)
    iva_amount_per_pack: int  # IVA portion per package (whole ARS)


def compute_unit_cost(
    pack_price: int,
    multiplier: int,
    blanco_bps: int = 6000,
    negro_bps: int = 4000,
    iva_rate_bps: int = 2100,
    discount_pct: int = 0,
    is_bulk: bool = False,
    bulk_reference_grams: int = 100,
) -> FiscalCostResult:
    """Compute real net unit cost accounting for Argentine fiscal split.

    All monetary values are in whole Argentine Pesos (integer ARS).
    Ratios are in basis points (6000 = 60%, 2100 = 21%).
    """
    if multiplier <= 0:
        raise ValueError(f"Multiplier must be positive, got {multiplier}")

    # factor_bps = negro_bps + (blanco_bps * (10000 + iva_rate_bps)) // 10000
    factor_bps = negro_bps + (blanco_bps * (10000 + iva_rate_bps)) // 10000

    # Real pack cost with discount (integer rounding)
    real_pack_cost_scaled = pack_price * factor_bps * (100 - discount_pct)
    real_pack_cost = (real_pack_cost_scaled + 500_000) // 1_000_000

    # IVA amount per pack
    iva_per_pack = (pack_price * blanco_bps * iva_rate_bps + 50_000_000) // 100_000_000

    # Unit cost
    if is_bulk and multiplier > 0:
        # Cost per bulk_reference_grams (e.g. per 100g)
        real_unit_cost = (
            real_pack_cost * bulk_reference_grams + multiplier // 2
        ) // multiplier
    else:
        # Cost per discrete unit
        real_unit_cost = (real_pack_cost + multiplier // 2) // multiplier

    return FiscalCostResult(
        effective_factor_bps=factor_bps,
        real_pack_cost=real_pack_cost,
        real_unit_cost=real_unit_cost,
        iva_amount_per_pack=iva_per_pack,
    )
