"""Pydantic / SQLModel schemas for inventory movements, merma, and audit trails."""

from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel

from server.models.inventory_ledger import InventoryMovementType
from server.models.products import ProductType


class StockReceivingRequest(SQLModel):
    """Inbound supplier replenishment request."""

    product_id: int = Field(description="Target product ID")
    quantity: int = Field(gt=0, description="Quantity to receive (units or grams)")
    reference_id: str | None = Field(
        default=None, description="Supplier invoice or shipment ID"
    )
    notes: str | None = Field(
        default=None, description="Optional notes regarding supplier or batch"
    )


class ShrinkageMermaRequest(SQLModel):
    """Inventory shrinkage / merma logging request."""

    product_id: int = Field(description="Target product ID")
    quantity: int = Field(
        gt=0,
        description="Amount lost to shrinkage (units/grams, positive int)",
    )
    notes: str = Field(
        description="Explanation for shrinkage (spillage, moisture loss, discard)"
    )
    reference_id: str | None = Field(
        default=None, description="Optional incident or shift ID"
    )


class StockAdjustmentRequest(SQLModel):
    """Manual physical audit count reconciliation request."""

    product_id: int = Field(description="Target product ID")
    counted_stock: int = Field(
        ge=0, description="Actual physical count found on shelf (units or grams)"
    )
    notes: str = Field(description="Audit justification or counter initials")
    reference_id: str | None = Field(
        default=None, description="Audit session reference ID"
    )


class StockReservationRequest(SQLModel):
    """Request to hold stock for an incoming delivery order."""

    product_id: int
    quantity: int = Field(gt=0, description="Quantity to reserve (units or grams)")
    order_reference_id: str = Field(
        description="External order ID (e.g. PedidosYa, Rappi)"
    )


class StockReleaseRequest(SQLModel):
    """Request to release reserved stock on order cancellation or timeout."""

    product_id: int
    quantity: int = Field(gt=0, description="Quantity to release")
    order_reference_id: str = Field(description="External order ID being released")


class StockFulfillRequest(SQLModel):
    """Finalize order fulfillment & dispatch, deducting reserved stock."""

    product_id: int
    quantity: int = Field(gt=0, description="Quantity fulfilled and dispatched")
    order_reference_id: str = Field(description="External order ID being fulfilled")


class POSSaleRequest(SQLModel):
    """Direct in-store POS checkout deduction (physical priority)."""

    product_id: int
    quantity: int = Field(gt=0, description="Units or grams sold at register")
    ticket_reference_id: str = Field(description="POS ticket or transaction ID")


class InventoryLedgerResponse(SQLModel):
    """Audit log item representing an immutable inventory ledger transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    movement_type: InventoryMovementType
    quantity_delta: int
    balance_after: int
    reference_id: str | None
    notes: str | None
    created_at: datetime


class StockAuditResponse(SQLModel):
    """Reconciliation view of physical stock, reservations, and ledger balance."""

    product_id: int
    sku: str
    name: str
    product_type: ProductType
    current_stock: int
    reserved_stock: int
    min_safety_buffer: int
    virtual_stock: int
    ledger_calculated_balance: int
    drift: int = Field(
        description="Difference between current_stock and sum of all ledger movements"
    )
    is_reconciled: bool = Field(
        description="True if current_stock equals sum of ledger history"
    )
