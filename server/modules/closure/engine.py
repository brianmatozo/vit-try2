"""Atomic database mutations for financial closures, cash movements, and arqueo."""

import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from server.core.exceptions import (
    ActiveClosureExistsError,
    EntityNotFoundError,
    RegisterClosedError,
)
from server.modules.catalog.models import Product
from server.modules.closure.models import (
    CashMovement,
    CashMovementType,
    ClosureStatus,
    FinancialClosure,
    PaymentMethod,
    POSTicket,
)
from server.modules.closure.schemas import (
    CashMovementCreateRequest,
    OpenClosureRequest,
    PerformArqueoRequest,
)
from server.modules.inventory.models import InventoryLedger, InventoryMovementType


async def open_closure(
    db: AsyncSession, req: OpenClosureRequest, user_id: int | None = None
) -> FinancialClosure:
    """Open a new register session, rejecting if one is already open."""
    existing_stmt = select(FinancialClosure).where(
        FinancialClosure.status == ClosureStatus.OPEN
    )
    existing = (await db.scalars(existing_stmt)).first()
    if existing:
        raise ActiveClosureExistsError(
            f"Ya existe una caja abierta iniciada el {existing.opened_at.isoformat()}."
        )

    closure = FinancialClosure(
        opened_at=datetime.now(timezone.utc),
        opened_by_user_id=user_id,
        initial_cash=req.initial_cash,
        expected_cash=req.initial_cash,
        notes=req.notes,
        status=ClosureStatus.OPEN,
    )
    db.add(closure)
    await db.commit()
    await db.refresh(closure)
    return closure


async def record_cash_movement(
    db: AsyncSession,
    closure_id: int,
    req: CashMovementCreateRequest,
    user_id: int | None = None,
) -> CashMovement:
    """Record cash in/out and update expected cash drawer balance."""
    stmt = (
        select(FinancialClosure)
        .where(FinancialClosure.id == closure_id)
        .with_for_update()
    )
    closure = (await db.scalars(stmt)).first()
    if not closure:
        raise EntityNotFoundError("FinancialClosure", closure_id)
    if closure.status != ClosureStatus.OPEN:
        raise RegisterClosedError(
            "No se pueden registrar movimientos en una caja cerrada."
        )

    if req.movement_type == CashMovementType.CASH_IN:
        closure.cash_in_amount += req.amount
    else:
        closure.cash_out_amount += req.amount

    closure.expected_cash = (
        closure.initial_cash
        + closure.cash_sales_amount
        + closure.cash_in_amount
        - closure.cash_out_amount
    )

    movement = CashMovement(
        closure_id=closure_id,
        movement_type=req.movement_type,
        amount=req.amount,
        reason=req.reason,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    return movement


async def aggregate_closure_metrics(
    db: AsyncSession, closure: FinancialClosure
) -> tuple[dict[str, int], int, int]:
    """Aggregate ticket sales by channel and shrinkage during session."""
    tickets_stmt = select(POSTicket).where(POSTicket.closure_id == closure.id)
    tickets = (await db.scalars(tickets_stmt)).all()

    sales = {
        "cash": 0,
        "card": 0,
        "qr": 0,
        "delivery": 0,
        "total": 0,
        "count": len(tickets),
    }
    for t in tickets:
        sales["total"] += t.total_amount
        if t.payment_method == PaymentMethod.CASH:
            sales["cash"] += t.total_amount
        elif t.payment_method == PaymentMethod.CARD:
            sales["card"] += t.total_amount
        elif t.payment_method == PaymentMethod.QR:
            sales["qr"] += t.total_amount
        elif t.payment_method == PaymentMethod.DELIVERY:
            sales["delivery"] += t.total_amount

    # Aggregate shrinkage movements since opened_at
    merma_stmt = (
        select(InventoryLedger, Product)
        .join(Product, col(InventoryLedger.product_id) == col(Product.id))
        .where(
            InventoryLedger.movement_type == InventoryMovementType.SHRINKAGE_MERMA,
            InventoryLedger.created_at >= closure.opened_at,
        )
    )
    merma_results = (await db.execute(merma_stmt)).all()
    merma_grams = 0
    merma_cost = 0
    for ledger_entry, prod in merma_results:
        qty = abs(ledger_entry.quantity_delta)
        merma_grams += qty
        if prod.product_type == "bulk":
            ref = prod.bulk_reference_grams or 100
            merma_cost += round((prod.unit_price * qty) / ref)
        else:
            merma_cost += round(prod.unit_price * qty)

    return sales, merma_grams, merma_cost


async def close_and_reconcile(
    db: AsyncSession,
    closure_id: int,
    req: PerformArqueoRequest,
    user_id: int | None = None,
) -> FinancialClosure:
    """Perform physical cash count arqueo and freeze closure snapshot."""
    stmt = (
        select(FinancialClosure)
        .where(FinancialClosure.id == closure_id)
        .with_for_update()
    )
    closure = (await db.scalars(stmt)).first()
    if not closure:
        raise EntityNotFoundError("FinancialClosure", closure_id)
    if closure.status != ClosureStatus.OPEN:
        raise RegisterClosedError("La caja ya se encuentra cerrada.")

    sales, merma_grams, merma_cost = await aggregate_closure_metrics(db, closure)

    expected = (
        closure.initial_cash
        + sales["cash"]
        + closure.cash_in_amount
        - closure.cash_out_amount
    )
    discrepancy = req.counted_cash - expected

    closure.closed_at = datetime.now(timezone.utc)
    closure.closed_by_user_id = user_id
    closure.cash_sales_amount = sales["cash"]
    closure.card_sales_amount = sales["card"]
    closure.qr_sales_amount = sales["qr"]
    closure.delivery_sales_amount = sales["delivery"]
    closure.total_sales_amount = sales["total"]
    closure.sales_count = sales["count"]
    closure.expected_cash = expected
    closure.counted_cash = req.counted_cash
    closure.discrepancy = discrepancy
    closure.status = ClosureStatus.CLOSED
    closure.cash_count_breakdown = json.dumps(req.breakdown or {})
    closure.merma_total_grams = merma_grams
    closure.merma_total_cost = merma_cost
    if req.notes:
        closure.notes = req.notes

    await db.commit()
    await db.refresh(closure)
    return closure


async def auto_close_session(db: AsyncSession, closure_id: int) -> FinancialClosure:
    """Scheduled automated closure at end of business day."""
    stmt = (
        select(FinancialClosure)
        .where(FinancialClosure.id == closure_id)
        .with_for_update()
    )
    closure = (await db.scalars(stmt)).first()
    if not closure:
        raise EntityNotFoundError("FinancialClosure", closure_id)
    if closure.status != ClosureStatus.OPEN:
        return closure

    sales, merma_grams, merma_cost = await aggregate_closure_metrics(db, closure)

    expected = (
        closure.initial_cash
        + sales["cash"]
        + closure.cash_in_amount
        - closure.cash_out_amount
    )

    closure.closed_at = datetime.now(timezone.utc)
    closure.cash_sales_amount = sales["cash"]
    closure.card_sales_amount = sales["card"]
    closure.qr_sales_amount = sales["qr"]
    closure.delivery_sales_amount = sales["delivery"]
    closure.total_sales_amount = sales["total"]
    closure.sales_count = sales["count"]
    closure.expected_cash = expected
    closure.status = ClosureStatus.CLOSED
    closure.auto_closed = True
    closure.merma_total_grams = merma_grams
    closure.merma_total_cost = merma_cost

    await db.commit()
    await db.refresh(closure)
    return closure
