from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from server.models.products import Product


class InventoryMovementType(str, Enum):
    """Types of inventory ledger movements for auditability."""

    SALE_POS = "sale_pos"  # In-store checkout
    DELIVERY_FULFILLED = "delivery_fulfilled"  # Delivery picked and dispatched
    SUPPLIER_RECEIVING = "receiving"  # Stock replenishment
    SHRINKAGE_MERMA = "shrinkage_merma"  # Spills, moisture loss, discard
    MANUAL_ADJUSTMENT = "manual_adjustment"  # Physical audit reconciliation


class InventoryLedger(SQLModel, table=True):
    """Append-only audit ledger tracking every stock mutation."""

    __tablename__ = "inventory_ledger"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    movement_type: InventoryMovementType
    quantity_delta: int  # Negative for sales/merma, positive for receiving
    balance_after: int  # Running balance at moment of transaction
    reference_id: str | None = Field(default=None)  # POS ticket # or order #
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    product: Optional["Product"] = Relationship(
        back_populates="ledger_entries",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
