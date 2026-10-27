"""Inbound replenishment, shrinkage merma, and stock adjustments."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlmodel import select

from server.core.exceptions import EntityNotFoundError, InvalidMovementError
from server.models.products import Product
from server.modules.inventory.models import InventoryLedger, InventoryMovementType
from server.modules.inventory.schemas import (
    ShrinkageMermaRequest,
    StockAdjustmentRequest,
    StockReceivingRequest,
)


async def get_locked_product(db: AsyncSession, product_id: int) -> Product:
    """Fetch product with row lock (SELECT FOR UPDATE) to prevent concurrency races.

    Uses noload('*') to avoid O(N) loading of entire ledger history.
    """
    stmt = (
        select(Product)
        .options(noload("*"))
        .where(Product.id == product_id)
        .with_for_update()
    )
    result = await db.scalars(stmt)
    product = result.first()
    if not product:
        raise EntityNotFoundError("Product", product_id)
    return product


_get_locked_product = get_locked_product


async def receive_stock(
    db: AsyncSession, req: StockReceivingRequest
) -> InventoryLedger:
    """Record inbound replenishment from a supplier into stock and audit ledger."""
    product = await get_locked_product(db, req.product_id)

    product.current_stock += req.quantity

    ledger_entry = InventoryLedger(
        product_id=req.product_id,
        movement_type=InventoryMovementType.SUPPLIER_RECEIVING,
        quantity_delta=req.quantity,
        balance_after=product.current_stock,
        reference_id=req.reference_id,
        notes=req.notes,
    )
    db.add(ledger_entry)
    await db.commit()
    await db.refresh(ledger_entry)
    return ledger_entry


async def log_merma(db: AsyncSession, req: ShrinkageMermaRequest) -> InventoryLedger:
    """Record shrinkage / merma (spillage, spoilage, evaporation) with audit trail."""
    product = await get_locked_product(db, req.product_id)

    if product.current_stock < req.quantity:
        raise InvalidMovementError(
            f"Cannot log merma of {req.quantity}; "
            f"product only has {product.current_stock} in stock"
        )

    product.current_stock -= req.quantity

    ledger_entry = InventoryLedger(
        product_id=req.product_id,
        movement_type=InventoryMovementType.SHRINKAGE_MERMA,
        quantity_delta=-req.quantity,
        balance_after=product.current_stock,
        reference_id=req.reference_id,
        notes=req.notes,
    )
    db.add(ledger_entry)
    await db.commit()
    await db.refresh(ledger_entry)
    return ledger_entry


async def adjust_stock(
    db: AsyncSession, req: StockAdjustmentRequest
) -> InventoryLedger:
    """Reconcile system stock to physical audit count."""
    product = await get_locked_product(db, req.product_id)

    delta = req.counted_stock - product.current_stock
    product.current_stock = req.counted_stock

    ledger_entry = InventoryLedger(
        product_id=req.product_id,
        movement_type=InventoryMovementType.MANUAL_ADJUSTMENT,
        quantity_delta=delta,
        balance_after=product.current_stock,
        reference_id=req.reference_id,
        notes=req.notes,
    )
    db.add(ledger_entry)
    await db.commit()
    await db.refresh(ledger_entry)
    return ledger_entry
