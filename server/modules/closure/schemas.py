"""Pydantic schemas for closures, arqueo reconciliation, and cash movements."""

from datetime import datetime, timezone

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from server.modules.closure.models import (
    CashMovementType,
    ClosureStatus,
    PaymentMethod,
)


class OpenClosureRequest(SQLModel):
    """Request payload to open a new register session."""

    initial_cash: int = Field(default=0, ge=0, description="Fondo inicial en ARS")
    notes: str | None = Field(default=None, description="Observaciones de apertura")


class PerformArqueoRequest(SQLModel):
    """Request payload to submit physical cash count and reconcile closure."""

    counted_cash: int = Field(ge=0, description="Efectivo físico contado en ARS")
    breakdown: dict[str, int] | None = Field(
        default=None, description="Conteo por denominación de billete"
    )
    notes: str | None = Field(default=None, description="Observaciones o justificación")


class CashMovementCreateRequest(SQLModel):
    """Request payload to record an intra-day cash movement in the drawer."""

    movement_type: CashMovementType = Field(description="Tipo: cash_in o cash_out")
    amount: int = Field(gt=0, description="Monto en ARS")
    reason: str = Field(min_length=2, description="Motivo o concepto del movimiento")


class CashMovementResponse(SQLModel):
    """Audit schema for a cash drawer movement."""

    id: int
    closure_id: int
    movement_type: CashMovementType
    amount: int
    reason: str
    user_id: int | None
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v


class POSTicketResponse(SQLModel):
    """Response schema for a completed POS checkout ticket."""

    id: int
    ticket_id: str
    closure_id: int
    payment_method: PaymentMethod
    total_amount: int
    cash_tendered: int | None
    change_returned: int | None
    items_count: int
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v


class FinancialClosureResponse(SQLModel):
    """Snapshot schema representing a financial closing session."""

    id: int
    opened_at: datetime
    closed_at: datetime | None
    opened_by_user_id: int | None
    closed_by_user_id: int | None
    initial_cash: int
    cash_sales_amount: int
    card_sales_amount: int
    qr_sales_amount: int
    delivery_sales_amount: int
    total_sales_amount: int
    sales_count: int
    cash_in_amount: int
    cash_out_amount: int
    expected_cash: int
    counted_cash: int | None
    discrepancy: int | None
    status: ClosureStatus
    auto_closed: bool
    notes: str | None
    cash_count_breakdown: str | None
    merma_total_grams: int
    merma_total_cost: int

    @field_validator("opened_at", "closed_at", mode="after")
    @classmethod
    def ensure_utc(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class ClosureSummaryResponse(SQLModel):
    """Real-time summary view of a closure session including live metrics."""

    closure: FinancialClosureResponse
    movements: list[CashMovementResponse]
    recent_tickets: list[POSTicketResponse]
    discrepancy_status: str
