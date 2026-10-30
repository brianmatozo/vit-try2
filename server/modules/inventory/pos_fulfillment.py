"""Virtual reservations, dispatch fulfillments, and POS checkout mutations."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlmodel import col, select

from server.core.exceptions import (
    EntityNotFoundError,
    InsufficientStockError,
    InsufficientVirtualStockError,
    RegisterClosedError,
)
from server.modules.catalog.models import Product
from server.modules.closure.models import (
    ClosureStatus,
    FinancialClosure,
    PaymentMethod,
    POSTicket,
)
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


def _calculate_line_total(product: Product, quantity: int) -> int:
    if product.product_type == "bulk":
        ref = product.bulk_reference_grams or 100
        return round((product.unit_price * quantity) / ref)
    return product.unit_price * quantity


def _update_closure_stats(
    closure: FinancialClosure, method: PaymentMethod, amount: int
) -> None:
    attr_map = {
        PaymentMethod.CASH: "cash_sales_amount",
        PaymentMethod.CARD: "card_sales_amount",
        PaymentMethod.QR: "qr_sales_amount",
        PaymentMethod.DELIVERY: "delivery_sales_amount",
    }
    field = attr_map.get(method, "cash_sales_amount")
    setattr(closure, field, getattr(closure, field) + amount)
    closure.total_sales_amount += amount
    closure.sales_count += 1
    closure.expected_cash = (
        closure.initial_cash
        + closure.cash_sales_amount
        + closure.cash_in_amount
        - closure.cash_out_amount
    )


async def record_pos_sale(db: AsyncSession, req: POSSaleRequest) -> InventoryLedger:
    """Record immediate in-store POS checkout deduction (physical priority)."""
    closure_stmt = (
        select(FinancialClosure)
        .where(FinancialClosure.status == ClosureStatus.OPEN)
        .with_for_update()
    )
    active_closure = (await db.scalars(closure_stmt)).first()
    if not active_closure:
        raise RegisterClosedError(
            "No hay una caja abierta. Debe abrir la caja para poder operar."
        )

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

    final_total = (
        req.total_amount
        if req.total_amount is not None
        else _calculate_line_total(product, req.quantity)
    )

    ticket = POSTicket(
        ticket_id=req.ticket_reference_id,
        closure_id=active_closure.id,  # type: ignore
        payment_method=req.payment_method,
        total_amount=final_total,
        items_count=1,
    )
    db.add(ticket)
    _update_closure_stats(active_closure, req.payment_method, final_total)

    await db.commit()
    await db.refresh(ledger_entry)
    return ledger_entry


async def record_pos_batch_sale(
    db: AsyncSession, req: POSBatchSaleRequest
) -> Sequence[InventoryLedger]:
    """Atomic multi-item POS checkout with deterministic product locks."""
    if not req.items:
        return []

    closure_stmt = (
        select(FinancialClosure)
        .where(FinancialClosure.status == ClosureStatus.OPEN)
        .with_for_update()
    )
    active_closure = (await db.scalars(closure_stmt)).first()
    if not active_closure:
        raise RegisterClosedError(
            "No hay una caja abierta. Debe abrir la caja para poder operar."
        )

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
    computed_total = 0
    for pid, qty in item_totals.items():
        product = products_by_id[pid]
        product.current_stock -= qty
        computed_total += _calculate_line_total(product, qty)

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

    final_total = req.total_amount if req.total_amount is not None else computed_total
    ticket = POSTicket(
        ticket_id=req.ticket_reference_id,
        closure_id=active_closure.id,  # type: ignore
        payment_method=req.payment_method,
        total_amount=final_total,
        cash_tendered=req.cash_tendered,
        change_returned=req.change_returned,
        items_count=len(req.items),
    )
    db.add(ticket)
    _update_closure_stats(active_closure, req.payment_method, final_total)

    await db.commit()
    for entry in ledger_entries:
        await db.refresh(entry)
    return ledger_entries
