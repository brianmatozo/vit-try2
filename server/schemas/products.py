"""Pydantic / SQLModel schemas for products and barcode parsing."""

from datetime import datetime

from pydantic import computed_field
from sqlmodel import Field, SQLModel

from server.models.products import ProductType


class ProductBase(SQLModel):
    sku: str = Field(description="Unique SKU or discrete barcode")
    name: str = Field(description="Product display name")
    unit_price: int = Field(
        gt=0,
        description=(
            "Unit price in whole Argentine Pesos (ARS). "
            "If bulk: price per reference weight."
        ),
    )
    bulk_reference_grams: int = Field(
        default=100,
        gt=0,
        description="Reference weight in grams for bulk pricing (default: 100g).",
    )
    plu_code: str | None = Field(
        default=None,
        description="4-digit in-store scale PLU code for bulk goods.",
    )
    product_type: ProductType = Field(
        default=ProductType.DISCRETE,
        description="Classification: 'discrete' for units, 'bulk' for weighed goods.",
    )
    min_safety_buffer: int = Field(
        default=0,
        ge=0,
        description="Stock buffer withheld from delivery channel synchronization.",
    )
    is_active: bool = Field(default=True)
    sync_pedidosya: bool = Field(default=True)
    sync_rappi: bool = Field(default=True)
    sync_vgo: bool = Field(default=True)
    sync_mercadolibre: bool = Field(default=False)


class ProductCreate(ProductBase):
    current_stock: int = Field(default=0, ge=0)


class ProductUpdate(SQLModel):
    sku: str | None = None
    name: str | None = None
    unit_price: int | None = Field(default=None, gt=0)
    bulk_reference_grams: int | None = Field(default=None, gt=0)
    plu_code: str | None = None
    product_type: ProductType | None = None
    min_safety_buffer: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    sync_pedidosya: bool | None = None
    sync_rappi: bool | None = None
    sync_vgo: bool | None = None
    sync_mercadolibre: bool | None = None


class ProductResponse(ProductBase):
    id: int
    current_stock: int
    reserved_stock: int
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def virtual_stock(self) -> int:
        """Virtual stock published to platforms: max(0, curr - res - buf)."""
        return max(0, self.current_stock - self.reserved_stock - self.min_safety_buffer)


class ProductScanResult(SQLModel):
    """Result of scanning an in-store barcode at POS or inventory."""

    raw_barcode: str
    is_embedded_weight: bool
    weight_grams: int | None = None
    product: ProductResponse
    line_total: int = Field(
        description="Total price in whole ARS for this scanned item/weight"
    )
