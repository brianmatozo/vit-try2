"""Read-only query builder for financial closures, movements, and tickets."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from server.core.exceptions import EntityNotFoundError
from server.modules.closure.engine import aggregate_closure_metrics
from server.modules.closure.models import (
    CashMovement,
    ClosureStatus,
    FinancialClosure,
    POSTicket,
)
from server.modules.closure.schemas import (
    CashMovementResponse,
    ClosureSummaryResponse,
    FinancialClosureResponse,
    POSTicketResponse,
)


async def get_active_closure(db: AsyncSession) -> FinancialClosure | None:
    """Retrieve the currently open register session, if any."""
    stmt = (
        select(FinancialClosure)
        .where(FinancialClosure.status == ClosureStatus.OPEN)
        .order_by(col(FinancialClosure.id).desc())
    )
    return (await db.scalars(stmt)).first()


async def get_closure_by_id(
    db: AsyncSession, closure_id: int
) -> FinancialClosure | None:
    """Retrieve a single closure record by ID."""
    stmt = select(FinancialClosure).where(FinancialClosure.id == closure_id)
    return (await db.scalars(stmt)).first()


async def list_closures(
    db: AsyncSession,
    status: ClosureStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[FinancialClosure]:
    """Retrieve paginated list of closures ordered newest first."""
    stmt = select(FinancialClosure)
    if status is not None:
        stmt = stmt.where(FinancialClosure.status == status)
    stmt = stmt.order_by(col(FinancialClosure.id).desc()).limit(limit).offset(offset)
    return (await db.scalars(stmt)).all()


async def list_closure_movements(
    db: AsyncSession, closure_id: int
) -> Sequence[CashMovement]:
    """Retrieve all intra-day cash movements for a given closure."""
    stmt = (
        select(CashMovement)
        .where(CashMovement.closure_id == closure_id)
        .order_by(col(CashMovement.created_at).asc())
    )
    return (await db.scalars(stmt)).all()


async def list_closure_tickets(
    db: AsyncSession, closure_id: int
) -> Sequence[POSTicket]:
    """Retrieve all checkout tickets completed under a given closure."""
    stmt = (
        select(POSTicket)
        .where(POSTicket.closure_id == closure_id)
        .order_by(col(POSTicket.created_at).desc())
    )
    return (await db.scalars(stmt)).all()


async def get_closure_live_summary(
    db: AsyncSession, closure_id: int
) -> ClosureSummaryResponse:
    """Compute real-time summary metrics for a closure session."""
    closure = await get_closure_by_id(db, closure_id)
    if not closure:
        raise EntityNotFoundError("FinancialClosure", closure_id)

    movements = await list_closure_movements(db, closure_id)
    tickets = await list_closure_tickets(db, closure_id)

    if closure.status == ClosureStatus.OPEN:
        sales, merma_grams, merma_cost = await aggregate_closure_metrics(db, closure)
        expected = (
            closure.initial_cash
            + sales["cash"]
            + closure.cash_in_amount
            - closure.cash_out_amount
        )
        closure_dict = closure.model_dump()
        closure_dict.update(
            {
                "cash_sales_amount": sales["cash"],
                "card_sales_amount": sales["card"],
                "qr_sales_amount": sales["qr"],
                "delivery_sales_amount": sales["delivery"],
                "total_sales_amount": sales["total"],
                "sales_count": sales["count"],
                "expected_cash": expected,
                "merma_total_grams": merma_grams,
                "merma_total_cost": merma_cost,
            }
        )
        closure_resp = FinancialClosureResponse.model_validate(closure_dict)
        discrepancy_status = "pending"
    else:
        closure_resp = FinancialClosureResponse.model_validate(closure)
        if closure.discrepancy is None:
            discrepancy_status = "pending"
        elif closure.discrepancy == 0:
            discrepancy_status = "exact"
        elif closure.discrepancy < 0:
            discrepancy_status = "shortage"
        else:
            discrepancy_status = "surplus"

    return ClosureSummaryResponse(
        closure=closure_resp,
        movements=[CashMovementResponse.model_validate(m) for m in movements],
        recent_tickets=[POSTicketResponse.model_validate(t) for t in tickets[:20]],
        discrepancy_status=discrepancy_status,
    )
