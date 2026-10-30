"""FastAPI router for financial closures, arqueo reconciliation, and cash movements."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.dependencies import get_async_db
from server.core.exceptions import EntityNotFoundError
from server.modules.closure import engine, queries, scheduler
from server.modules.closure.models import ClosureStatus
from server.modules.closure.schemas import (
    CashMovementCreateRequest,
    CashMovementResponse,
    ClosureSummaryResponse,
    FinancialClosureResponse,
    OpenClosureRequest,
    PerformArqueoRequest,
    POSTicketResponse,
)

router = APIRouter(prefix="/closure", tags=["Financial Closing"])


@router.get(
    "/active",
    response_model=ClosureSummaryResponse | None,
    summary="Get active register session",
    operation_id="getActiveClosure",
)
async def get_active_closure_endpoint(
    db: AsyncSession = Depends(get_async_db),
) -> ClosureSummaryResponse | None:
    active = await queries.get_active_closure(db)
    if not active or active.id is None:
        return None
    return await queries.get_closure_live_summary(db, active.id)


@router.post(
    "/open",
    response_model=FinancialClosureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open new register session",
    operation_id="openClosure",
)
async def open_closure_endpoint(
    req: OpenClosureRequest,
    db: AsyncSession = Depends(get_async_db),
) -> FinancialClosureResponse:
    closure = await engine.open_closure(db, req)
    return FinancialClosureResponse.model_validate(closure)


@router.get(
    "/{closure_id}/summary",
    response_model=ClosureSummaryResponse,
    summary="Get live closure summary",
    operation_id="getClosureSummary",
)
async def get_closure_summary_endpoint(
    closure_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> ClosureSummaryResponse:
    return await queries.get_closure_live_summary(db, closure_id)


@router.post(
    "/{closure_id}/close",
    response_model=FinancialClosureResponse,
    summary="Perform arqueo and close register session",
    operation_id="closeClosure",
)
async def close_closure_endpoint(
    closure_id: int,
    req: PerformArqueoRequest,
    db: AsyncSession = Depends(get_async_db),
) -> FinancialClosureResponse:
    closed = await engine.close_and_reconcile(db, closure_id, req)
    return FinancialClosureResponse.model_validate(closed)


@router.post(
    "/{closure_id}/movements",
    response_model=CashMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record cash in / cash out movement",
    operation_id="recordCashMovement",
)
async def record_cash_movement_endpoint(
    closure_id: int,
    req: CashMovementCreateRequest,
    db: AsyncSession = Depends(get_async_db),
) -> CashMovementResponse:
    movement = await engine.record_cash_movement(db, closure_id, req)
    return CashMovementResponse.model_validate(movement)


@router.get(
    "/{closure_id}/movements",
    response_model=list[CashMovementResponse],
    summary="List cash movements for closure",
    operation_id="listClosureMovements",
)
async def list_closure_movements_endpoint(
    closure_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> list[CashMovementResponse]:
    movements = await queries.list_closure_movements(db, closure_id)
    return [CashMovementResponse.model_validate(m) for m in movements]


@router.get(
    "/{closure_id}/tickets",
    response_model=list[POSTicketResponse],
    summary="List checkout tickets for closure",
    operation_id="listClosureTickets",
)
async def list_closure_tickets_endpoint(
    closure_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> list[POSTicketResponse]:
    tickets = await queries.list_closure_tickets(db, closure_id)
    return [POSTicketResponse.model_validate(t) for t in tickets]


@router.get(
    "/history",
    response_model=list[FinancialClosureResponse],
    summary="List historical closures",
    operation_id="listClosuresHistory",
)
async def list_closures_history_endpoint(
    status: ClosureStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_async_db),
) -> list[FinancialClosureResponse]:
    closures = await queries.list_closures(
        db, status=status, limit=limit, offset=offset
    )
    return [FinancialClosureResponse.model_validate(c) for c in closures]


@router.get(
    "/{closure_id}",
    response_model=FinancialClosureResponse,
    summary="Get single closure",
    operation_id="getClosureById",
)
async def get_closure_by_id_endpoint(
    closure_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> FinancialClosureResponse:
    closure = await queries.get_closure_by_id(db, closure_id)
    if not closure:
        raise EntityNotFoundError("FinancialClosure", closure_id)
    return FinancialClosureResponse.model_validate(closure)


@router.post(
    "/cron/check",
    summary="Trigger scheduled hours evaluation",
    operation_id="triggerClosureScheduleCheck",
)
async def trigger_schedule_check_endpoint(
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str | int | None]:
    return await scheduler.check_and_apply_schedule(db)
