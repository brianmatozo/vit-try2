"""Temporary backward-compatibility bridge. Purged in Phase 5."""

from server.modules.inventory.schemas import (
    InventoryLedgerResponse,
    InventoryMovementType,
    POSBatchSaleRequest,
    POSSaleItem,
    POSSaleRequest,
    ProductType,
    ShrinkageMermaRequest,
    StockAdjustmentRequest,
    StockAuditResponse,
    StockFulfillRequest,
    StockReceivingRequest,
    StockReleaseRequest,
    StockReservationRequest,
)

__all__ = [
    "InventoryLedgerResponse",
    "InventoryMovementType",
    "POSBatchSaleRequest",
    "POSSaleItem",
    "POSSaleRequest",
    "ProductType",
    "ShrinkageMermaRequest",
    "StockAdjustmentRequest",
    "StockAuditResponse",
    "StockFulfillRequest",
    "StockReceivingRequest",
    "StockReleaseRequest",
    "StockReservationRequest",
]
