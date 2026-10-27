"""Virtual reservations, dispatch fulfillments, and POS checkout mutations."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlmodel import col, select

from server.core.exceptions import (
    EntityNotFoundError,
    InsufficientStockError,
    InsufficientVirtualStockError,
)
from server.modules.catalog.models import Product
from server.modules.inventory.models import InventoryLedger, InventoryMovementType
from server.modules.inventory.movements import get_locked_product
from server.modules.inventory.schemas import (
    POSBatchSaleRequest,
    POSSaleRequest,
    StockFulfillRequest,
    StockReleaseRequest,
    StockReservationRequest,
)


async def reserve_stock(db: AsyncSession, req: StockReservationRequest) -> Product:
    """Hold stock for an incoming delivery order subject to virtual safety buffer."""
    product = await get_locked_product(db, req.product_id)

    virtual_stock = max(
        0, product.current_stock - product.reserved_stock - product.min_safety_buffer
    )
    if virtual_stock < req.quantity:
        raise InsufficientVirtualStockError(
            requested=req.quantity, available=virtual_stock
        )

    product.reserved_stock += req.quantity
    await db.commit()
    await db.refresh(product)
    return product


async def release_stock(db: AsyncSession, req: StockReleaseRequest) -> Product:
    """Release previously held stock on order cancellation or TTL expiration."""
    product = await get_locked_product(db, req.product_id)

    product.reserved_stock = max(0, product.reserved_stock - req.quantity)
    await db.commit()
    await db.refresh(product)
    return product


async def fulfill_order(db: AsyncSession, req: StockFulfillRequest) -> InventoryLedger:
    """Finalize picking & dispatch: decrement reserved & current stock, log ledger."""
    product = await get_locked_product(db, req.product_id)

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
    product = await get_locked_product(db, req.product_id)

    if product.current_stock < req.quantity:
        raise InsufficientStockError(
            item_name=product.name,
            requested=req.quantity,
            available=product.current_stock,
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

    item_totals: dict[int, int] = {}
    for item in req.items:
        item_totals[item.product_id] = (
            item_totals.get(item.product_id, 0) + item.quantity
        )

    sorted_product_ids = sorted(item_totals.keys())

    stmt = (
        select(Product)
        .options(noload("*"))
        .where(col(Product.id).in_(sorted_product_ids))
        .with_for_update()
    )
    products_by_id = {p.id: p for p in (await db.scalars(stmt)).all()}

    for pid, qty in item_totals.items():
        product = products_by_id.get(pid)
        if not product:
            raise EntityNotFoundError("Product", pid)
        if product.current_stock < qty:
            raise InsufficientStockError(
                item_name=f"{product.name} (PLU: {product.sku})",
                requested=qty,
                available=product.current_stock,
            )

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
