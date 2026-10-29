from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlmodel import select

from server.core.exceptions import (
    EntityNotFoundError,
    InvalidMovementError,
    RemitoConflictError,
)
from server.modules.catalog.models import Product
from server.modules.inventory.models import InventoryLedger
from server.modules.remitos.matching import upsert_alias_mapping
from server.modules.remitos.models import (
    Remito,
    RemitoItem,
    RemitoStatus,
)


async def _get_staged_remito(db: AsyncSession, remito_id: int) -> Remito:
    """Fetch locked remito and assert it is in STAGED status."""
    q = select(Remito).where(Remito.id == remito_id).with_for_update()
    if not (remito := (await db.scalars(q)).first()):
        raise EntityNotFoundError("Remito", remito_id)
    if remito.status != RemitoStatus.STAGED:
        raise RemitoConflictError(f"Remito is {remito.status}, expected staged")
    return remito


async def confirm_remito(db: AsyncSession, remito_id: int) -> Remito:
    """Atomic double-entry stock commitment and alias dictionary caching."""
    remito = await _get_staged_remito(db, remito_id)
    items = (
        await db.scalars(select(RemitoItem).where(RemitoItem.remito_id == remito_id))
    ).all()

    for it in items:
        if it.quantity_to_commit > 0 and not it.product_id:
            raise InvalidMovementError(
                f"Item '{it.raw_description}' is not linked to any product"
            )

    for it in items:
        if it.quantity_to_commit <= 0 or not it.product_id:
            continue

        prod_q = select(Product).options(noload("*")).where(Product.id == it.product_id)
        prod = (await db.scalars(prod_q.with_for_update())).one()
        assert prod.id is not None
        prod.current_stock += it.quantity_to_commit
        prod.last_cost = it.calculated_unit_cost

        remito_ref = remito.remito_number or remito.id
        db.add(
            InventoryLedger(
                product_id=prod.id,
                movement_type="receiving",
                quantity_delta=it.quantity_to_commit,
                balance_after=prod.current_stock,
                reference_id=f"REMITO-{remito.id}",
                notes=f"Remito {remito_ref}: {it.raw_description[:40]}",
            )
        )

        await upsert_alias_mapping(
            db,
            remito.supplier_name,
            it.raw_description,
            prod.id,
            it.multiplier,
            it.package_type,
            it.target_unit_type,
        )

    remito.status = RemitoStatus.COMMITTED
    remito.committed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(remito)
    return remito


async def reject_remito(db: AsyncSession, remito_id: int) -> Remito:
    """Discard a staged remito."""
    remito = await _get_staged_remito(db, remito_id)
    remito.status = RemitoStatus.REJECTED
    await db.commit()
    await db.refresh(remito)
    return remito
