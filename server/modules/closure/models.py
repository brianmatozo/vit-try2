"""SQLModel tables for financial closures, cash drawer movements, and POS tickets."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class ClosureStatus(str, Enum):
    """Status lifecycle of a financial register session."""

    OPEN = "open"
    CLOSED = "closed"


class PaymentMethod(str, Enum):
    """Accepted customer payment methods."""

    CASH = "cash"
    CARD = "card"
    QR = "qr"
    DELIVERY = "delivery"


class CashMovementType(str, Enum):
    """Types of physical cash drawer movements."""

    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"


class FinancialClosure(SQLModel, table=True):
    """Financial register closing session snapshot."""

    __tablename__ = "financial_closures"

    id: int | None = Field(default=None, primary_key=True)
    opened_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    closed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
    )
    opened_by_user_id: int | None = Field(default=None, foreign_key="users.id")
    closed_by_user_id: int | None = Field(default=None, foreign_key="users.id")

    # Initial float & revenue breakdowns in whole ARS
    initial_cash: int = Field(default=0, ge=0)
    cash_sales_amount: int = Field(default=0, ge=0)
    card_sales_amount: int = Field(default=0, ge=0)
    qr_sales_amount: int = Field(default=0, ge=0)
    delivery_sales_amount: int = Field(default=0, ge=0)
    total_sales_amount: int = Field(default=0, ge=0)
    sales_count: int = Field(default=0, ge=0)

    # Cash drawer movements
    cash_in_amount: int = Field(default=0, ge=0)
    cash_out_amount: int = Field(default=0, ge=0)

    # Arqueo reconciliation
    expected_cash: int = Field(default=0)
    counted_cash: int | None = Field(default=None)
    discrepancy: int | None = Field(default=None)

    status: ClosureStatus = Field(default=ClosureStatus.OPEN, index=True)
    auto_closed: bool = Field(default=False)
    notes: str | None = None
    cash_count_breakdown: str | None = (
        None  # JSON text for cross-engine SQLite/Postgres compatibility
    )

    # Bulk shrinkage audit summary
    merma_total_grams: int = Field(default=0, ge=0)
    merma_total_cost: int = Field(default=0, ge=0)


class CashMovement(SQLModel, table=True):
    """Intra-day cash deposit or withdrawal from the register drawer."""

    __tablename__ = "cash_movements"

    id: int | None = Field(default=None, primary_key=True)
    closure_id: int = Field(foreign_key="financial_closures.id", index=True)
    movement_type: CashMovementType = Field(index=True)
    amount: int = Field(gt=0, description="Amount in whole ARS")
    reason: str = Field(min_length=2, description="Explanation for movement")
    user_id: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class POSTicket(SQLModel, table=True):
    """Metadata record for a completed POS checkout ticket."""

    __tablename__ = "pos_tickets"

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: str = Field(index=True, unique=True, description="POS reference code")
    closure_id: int = Field(foreign_key="financial_closures.id", index=True)
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH, index=True)
    total_amount: int = Field(ge=0, description="Total ticket amount in ARS")
    cash_tendered: int | None = Field(
        default=None, description="Cash handed over in ARS"
    )
    change_returned: int | None = Field(
        default=None, description="Change returned in ARS"
    )
    items_count: int = Field(default=1, ge=1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    notes: str | None = None
