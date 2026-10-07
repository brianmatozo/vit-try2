"""Transactional double-entry inventory engine services."""

from collections.abc import Sequence

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlmodel import col, select

from server.models.inventory_ledger import InventoryLedger, InventoryMovementType
from server.models.products import Product
from server.schemas.inventory import (
    POSBatchSaleRequest,
    POSSaleRequest,
    ShrinkageMermaRequest,
    StockAdjustmentRequest,
    StockAuditResponse,
    StockFulfillRequest,
    StockReceivingRequest,
    StockReleaseRequest,
    StockReservationRequest,
)


async def _get_locked_product(db: AsyncSession, product_id: int) -> Product:
    """Fetch product with row lock (SELECT FOR UPDATE) to prevent concurrency races.

    Uses noload(Product.ledger_entries) to avoid O(N) loading of entire ledger history.
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
        raise ValueError(f"Product with ID {product_id} not found")
    return product


async def receive_stock(
    db: AsyncSession, req: StockReceivingRequest
) -> InventoryLedger:
    """Record inbound replenishment from a supplier into stock and audit ledger."""
    product = await _get_locked_product(db, req.product_id)

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
    product = await _get_locked_product(db, req.product_id)

    if product.current_stock < req.quantity:
        raise ValueError(
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
    product = await _get_locked_product(db, req.product_id)

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


async def reserve_stock(db: AsyncSession, req: StockReservationRequest) -> Product:
    """Hold stock for an incoming delivery order subject to virtual safety buffer."""
    product = await _get_locked_product(db, req.product_id)

    virtual_stock = max(
        0, product.current_stock - product.reserved_stock - product.min_safety_buffer
    )
    if virtual_stock < req.quantity:
        raise ValueError(
            f"Insufficient virtual stock for reservation. "
            f"Available: {virtual_stock}, Requested: {req.quantity}"
        )

    product.reserved_stock += req.quantity
    await db.commit()
    await db.refresh(product)
    return product


async def release_stock(db: AsyncSession, req: StockReleaseRequest) -> Product:
    """Release previously held stock on order cancellation or TTL expiration."""
    product = await _get_locked_product(db, req.product_id)

    product.reserved_stock = max(0, product.reserved_stock - req.quantity)
    await db.commit()
    await db.refresh(product)
    return product


async def fulfill_order(db: AsyncSession, req: StockFulfillRequest) -> InventoryLedger:
    """Finalize picking & dispatch: decrement reserved & current stock, log ledger."""
    product = await _get_locked_product(db, req.product_id)

    product.reserved_stock = max(0, product.reserved_stock - req.quantity)
    product.current_stock = max(0, product.current_stock - req.quantity)

    ledger_entry = InventoryLedger(
        product_id=req.product_id,
        movement_type=InventoryMovementType.DELIVERY_FULFILLED,
        quantity_delta=-req.quantity,
        balance_after=product.current_stock,
        reference_id=req.order_reference_id,
        notes="Order dispatched and fulfilled",
    )
    db.add(ledger_entry)
    await db.commit()
    await db.refresh(ledger_entry)
    return ledger_entry


async def record_pos_sale(db: AsyncSession, req: POSSaleRequest) -> InventoryLedger:
    """Record immediate in-store POS checkout deduction (physical priority)."""
    product = await _get_locked_product(db, req.product_id)

    if product.current_stock < req.quantity:
        raise ValueError(
            f"Physical stock depleted: requested {req.quantity}, "
            f"available {product.current_stock}"
        )

    product.current_stock -= req.quantity

    ledger_entry = InventoryLedger(
        product_id=req.product_id,
        movement_type=InventoryMovementType.SALE_POS,
        quantity_delta=-req.quantity,
        balance_after=product.current_stock,
        reference_id=req.ticket_reference_id,
        notes="In-store register sale",
    )
    db.add(ledger_entry)
    await db.commit()
    await db.refresh(ledger_entry)
    return ledger_entry


async def record_pos_batch_sale(
    db: AsyncSession, req: POSBatchSaleRequest
) -> Sequence[InventoryLedger]:
    """Atomic multi-item POS checkout deduction.

    Locks all products in a single batch query (sorted deterministically
    to prevent deadlocks), validates physical stock across all items, deducts
    stock, and commits an atomic batch of inventory ledger movements in a
    single transaction.
    """
    if not req.items:
        return []

    # Aggregate quantities by product_id in case the same item appears multiple times
    item_totals: dict[int, int] = {}
    for item in req.items:
        item_totals[item.product_id] = (
            item_totals.get(item.product_id, 0) + item.quantity
        )

    # Sort product IDs deterministically to eliminate deadlocks
    sorted_product_ids = sorted(item_totals.keys())

    # Lock all target products in a single bulk query without pulling ledger history
    stmt = (
        select(Product)
        .options(noload("*"))
        .where(col(Product.id).in_(sorted_product_ids))
        .with_for_update()
    )
    products_by_id = {p.id: p for p in (await db.scalars(stmt)).all()}

    # Verify all products exist and have sufficient physical stock
    for pid, qty in item_totals.items():
        product = products_by_id.get(pid)
        if not product:
            raise ValueError(f"Product with ID {pid} not found")
        if product.current_stock < qty:
            raise ValueError(
                f"Physical stock depleted for '{product.name}' (SKU: {product.sku}): "
                f"requested {qty}, available {product.current_stock}"
            )

    # Perform in-memory stock mutations and construct ledger entries
    ledger_entries: list[InventoryLedger] = []
    for pid, qty in item_totals.items():
        product = products_by_id[pid]
        product.current_stock -= qty

        entry = InventoryLedger(
            product_id=pid,
            movement_type=InventoryMovementType.SALE_POS,
            quantity_delta=-qty,
            balance_after=product.current_stock,
            reference_id=req.ticket_reference_id,
            notes="In-store register sale",
        )
        ledger_entries.append(entry)

    db.add_all(ledger_entries)
    await db.commit()
    for entry in ledger_entries:
        await db.refresh(entry)
    return ledger_entries


async def audit_product_stock(db: AsyncSession, product_id: int) -> StockAuditResponse:
    """Automated stock calculation view comparing stock against ledger history."""
    product = await _get_locked_product(db, product_id)

    sum_stmt = select(func.coalesce(func.sum(InventoryLedger.quantity_delta), 0)).where(
        InventoryLedger.product_id == product_id
    )
    ledger_balance = (await db.scalars(sum_stmt)).first() or 0

    virtual_stock = max(
        0, product.current_stock - product.reserved_stock - product.min_safety_buffer
    )
    drift = product.current_stock - ledger_balance

    return StockAuditResponse(
        product_id=product_id,
        sku=product.sku,
        name=product.name,
        product_type=product.product_type,
        current_stock=product.current_stock,
        reserved_stock=product.reserved_stock,
        min_safety_buffer=product.min_safety_buffer,
        virtual_stock=virtual_stock,
        ledger_calculated_balance=ledger_balance,
        drift=drift,
        is_reconciled=(drift == 0),
    )


async def get_ledger_history(
    db: AsyncSession,
    product_id: int | None = None,
    movement_type: InventoryMovementType | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[InventoryLedger]:
    """Query paginated append-only inventory ledger history."""
    stmt = select(InventoryLedger)
    if product_id is not None:
        stmt = stmt.where(InventoryLedger.product_id == product_id)
    if movement_type is not None:
        stmt = stmt.where(InventoryLedger.movement_type == movement_type)

    stmt = stmt.order_by(col(InventoryLedger.id).desc()).limit(limit).offset(offset)
    result = await db.scalars(stmt)
    return result.all()
