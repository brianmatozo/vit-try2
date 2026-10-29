from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.core.exceptions import EntityNotFoundError
from server.modules.remitos.engine import (
    _get_staged_remito,
    confirm_remito,
    reject_remito,
)
from server.modules.remitos.fiscal import compute_unit_cost
from server.modules.remitos.models import (
    MatchStrategy,
    Remito,
    RemitoItem,
    TargetUnitType,
)
from server.modules.remitos.schemas import (
    RemitoHeaderUpdate,
    RemitoItemUpdate,
)
from server.modules.remitos.staging import scan_and_stage_remito

__all__ = [
    "_get_staged_remito",
    "confirm_remito",
    "reject_remito",
    "scan_and_stage_remito",
    "update_remito_header",
    "update_remito_item",
]


async def update_remito_item(
    db: AsyncSession, remito_id: int, item_id: int, req: RemitoItemUpdate
) -> RemitoItem:
    """Inline update a staged remito line item."""
    q = select(RemitoItem).where(
        RemitoItem.id == item_id, RemitoItem.remito_id == remito_id
    )
    if not (item := (await db.scalars(q)).first()):
        raise EntityNotFoundError("RemitoItem", item_id)

    remito = await _get_staged_remito(db, remito_id)

    if req.product_id is not None:
        item.product_id, item.match_strategy = (
            req.product_id,
            MatchStrategy.MANUAL_OVERRIDE,
        )
        item.match_confidence, item.is_verified_by_user = 100, True

    for attr in (
        "multiplier",
        "package_type",
        "target_unit_type",
        "effective_quantity",
        "is_verified_by_user",
    ):
        if (v := getattr(req, attr, None)) is not None:
            setattr(item, attr, v)

    item.quantity_to_commit = item.effective_quantity * item.multiplier
    cost = compute_unit_cost(
        item.extracted_unit_cost,
        item.multiplier,
        remito.fiscal_blanco_bps,
        remito.fiscal_negro_bps,
        remito.iva_rate_bps,
        is_bulk=item.target_unit_type == TargetUnitType.BULK_GRAMS,
    )
    item.calculated_unit_cost = cost.real_unit_cost
    await db.commit()
    await db.refresh(item)
    return item


async def update_remito_header(
    db: AsyncSession, remito_id: int, req: RemitoHeaderUpdate
) -> Remito:
    """Update remito header (fiscal split or notes) and recalculate item costs."""
    remito = await _get_staged_remito(db, remito_id)

    if req.fiscal_blanco_pct is not None:
        remito.fiscal_blanco_bps = req.fiscal_blanco_pct * 100
    if req.fiscal_negro_pct is not None:
        remito.fiscal_negro_bps = req.fiscal_negro_pct * 100
    if req.iva_pct is not None:
        remito.iva_rate_bps = req.iva_pct * 100
    if req.notes is not None:
        remito.notes = req.notes

    items = (
        await db.scalars(select(RemitoItem).where(RemitoItem.remito_id == remito_id))
    ).all()
    total_real = 0
    for it in items:
        cost = compute_unit_cost(
            it.extracted_unit_cost,
            it.multiplier,
            remito.fiscal_blanco_bps,
            remito.fiscal_negro_bps,
            remito.iva_rate_bps,
            is_bulk=it.target_unit_type == TargetUnitType.BULK_GRAMS,
        )
        it.calculated_unit_cost = cost.real_unit_cost
        total_real += it.effective_quantity * cost.real_pack_cost

    remito.total_real_amount = total_real
    await db.commit()
    await db.refresh(remito)
    return remito
