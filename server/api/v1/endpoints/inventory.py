"""API endpoints for inventory ledger movements, receiving, merma, and stock audit."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.dependencies import get_async_db
from server.models.inventory_ledger import InventoryMovementType
from server.schemas.inventory import (
    InventoryLedgerResponse,
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
from server.schemas.products import ProductResponse
from server.services import inventory_services as service

router = APIRouter(prefix="/inventory", tags=["Inventory Engine"])


@router.post(
    "/receive",
    response_model=InventoryLedgerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receive supplier stock",
    description="Replenish catalog item inventory from an inbound supplier delivery.",
    operation_id="receiveStock",
)
async def receive_stock(
    req: StockReceivingRequest,
    db: AsyncSession = Depends(get_async_db),
) -> InventoryLedgerResponse:
    try:
        entry = await service.receive_stock(db, req)
        return InventoryLedgerResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/merma",
    response_model=InventoryLedgerResponse,
    status_code=status.HTTP_200_OK,
    summary="Log shrinkage / merma",
    description=(
        "Deduct inventory lost to spillage, moisture loss, expiration, or tasting."
    ),
    operation_id="logMerma",
)
async def log_merma(
    req: ShrinkageMermaRequest,
    db: AsyncSession = Depends(get_async_db),
) -> InventoryLedgerResponse:
    try:
        entry = await service.log_merma(db, req)
        return InventoryLedgerResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/adjust",
    response_model=InventoryLedgerResponse,
    status_code=status.HTTP_200_OK,
    summary="Manual stock adjustment / reconciliation",
    description="Set stock to physical audit count and record delta.",
    operation_id="adjustStock",
)
async def adjust_stock(
    req: StockAdjustmentRequest,
    db: AsyncSession = Depends(get_async_db),
) -> InventoryLedgerResponse:
    try:
        entry = await service.adjust_stock(db, req)
        return InventoryLedgerResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/reserve",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Reserve virtual stock",
    description="Hold available virtual stock for incoming delivery orders.",
    operation_id="reserveStock",
)
async def reserve_stock(
    req: StockReservationRequest,
    db: AsyncSession = Depends(get_async_db),
) -> ProductResponse:
    try:
        product = await service.reserve_stock(db, req)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/release",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Release stock reservation",
    description="Release previously held stock on order cancellation or timeout.",
    operation_id="releaseStock",
)
async def release_stock(
    req: StockReleaseRequest,
    db: AsyncSession = Depends(get_async_db),
) -> ProductResponse:
    try:
        product = await service.release_stock(db, req)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/fulfill",
    response_model=InventoryLedgerResponse,
    status_code=status.HTTP_200_OK,
    summary="Fulfill and dispatch delivery order",
    description="Decrements reserved & current stock upon picking and packaging.",
    operation_id="fulfillOrder",
)
async def fulfill_order(
    req: StockFulfillRequest,
    db: AsyncSession = Depends(get_async_db),
) -> InventoryLedgerResponse:
    try:
        entry = await service.fulfill_order(db, req)
        return InventoryLedgerResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/sale-pos",
    response_model=InventoryLedgerResponse,
    status_code=status.HTTP_200_OK,
    summary="Record in-store POS sale",
    description="Deduct inventory for cashier register sales (physical priority).",
    operation_id="recordPOSSale",
)
async def record_pos_sale(
    req: POSSaleRequest,
    db: AsyncSession = Depends(get_async_db),
) -> InventoryLedgerResponse:
    try:
        entry = await service.record_pos_sale(db, req)
        return InventoryLedgerResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/sale-pos/batch",
    response_model=list[InventoryLedgerResponse],
    status_code=status.HTTP_200_OK,
    summary="Record atomic multi-item POS sale",
    description=(
        "Batch deduct inventory for full shopping cart in a single atomic transaction."
    ),
    operation_id="recordPOSBatchSale",
)
async def record_pos_batch_sale(
    req: POSBatchSaleRequest,
    db: AsyncSession = Depends(get_async_db),
) -> list[InventoryLedgerResponse]:
    try:
        entries = await service.record_pos_batch_sale(db, req)
        return [InventoryLedgerResponse.model_validate(e) for e in entries]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/audit/{product_id}",
    response_model=StockAuditResponse,
    summary="Audit product stock & ledger balance",
    description="Compare stock against complete ledger history to detect drift.",
    operation_id="auditProductStock",
)
async def audit_product_stock(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> StockAuditResponse:
    try:
        return await service.audit_product_stock(db, product_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/ledger",
    response_model=list[InventoryLedgerResponse],
    summary="Query inventory ledger",
    description="Retrieve immutable ledger history with optional filtering.",
    operation_id="getInventoryLedger",
)
async def get_inventory_ledger(
    product_id: int | None = Query(default=None, description="Filter by product ID"),
    movement_type: InventoryMovementType | None = Query(
        default=None, description="Filter by movement type"
    ),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_async_db),
) -> list[InventoryLedgerResponse]:
    entries = await service.get_ledger_history(
        db,
        product_id=product_id,
        movement_type=movement_type,
        limit=limit,
        offset=offset,
    )
    return [InventoryLedgerResponse.model_validate(e) for e in entries]
