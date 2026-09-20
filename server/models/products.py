from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from server.models.inventory_ledger import InventoryLedger


class ProductType(str, Enum):
    """Product classification distinguishing discrete units from weighted bulk goods."""

    DISCRETE = "discrete"  # Sold by unit (box of cookies, tea)
    BULK = "bulk"  # Sold by weight (almonds, chia seeds)


class Product(SQLModel, table=True):
    """Database model representing a catalog item (discrete or bulk)."""

    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    sku: str = Field(unique=True, index=True)
    plu_code: str | None = Field(default=None, index=True)
    name: str = Field(index=True)
    product_type: ProductType = Field(default=ProductType.DISCRETE)

    # Pricing (stored in integer whole ARS, no centavos)
    # If discrete: price per single unit
    # If bulk: price per reference weight (e.g. 100 grams)
    unit_price: int
    bulk_reference_grams: int = Field(default=100)

    # Inventory state (current calculated balance)
    current_stock: int = Field(default=0)
    reserved_stock: int = Field(default=0)
    min_safety_buffer: int = Field(default=0)

    # External Channel Flags
    is_active: bool = Field(default=True)
    sync_pedidosya: bool = Field(default=True)
    sync_rappi: bool = Field(default=True)
    sync_vgo: bool = Field(default=True)
    sync_mercadolibre: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    ledger_entries: list["InventoryLedger"] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
