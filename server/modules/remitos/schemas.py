from datetime import datetime

from pydantic import BaseModel, Field

from server.modules.remitos.models import (
    MatchStrategy,
    RemitoStatus,
    TargetUnitType,
)


class ExtractedLineItem(BaseModel):
    """Single printed line item extracted from the delivery receipt by Vision."""

    line_index: int = Field(description="0-based line position")
    raw_description: str = Field(
        description="Full item description as printed (e.g. 'Barritas x 10 u')"
    )
    quantity: int = Field(default=1, description="Number of wholesale packages")
    unit_cost: int = Field(
        default=0, description="Cost per wholesale package in whole ARS"
    )
    line_total: int = Field(default=0, description="Line total in whole ARS")
    confidence: int = Field(default=90, description="Extraction confidence 0-100")


class ExtractedFiscalInfo(BaseModel):
    """Fiscal split and total information from receipt header/footer."""

    subtotal: int | None = Field(default=None, description="Subtotal before tax")
    total: int | None = Field(default=None, description="Document total in whole ARS")
    discount_percentage: int | None = Field(
        default=None, description="Global discount %"
    )
    blanco_percentage: int | None = Field(
        default=None, description="Formal fraction % (e.g. 60)"
    )
    negro_percentage: int | None = Field(
        default=None, description="Informal fraction % (e.g. 40)"
    )
    iva_percentage: int | None = Field(default=None, description="IVA rate % (e.g. 21)")


class RemitoVisionOutput(BaseModel):
    """Complete structured extraction from receipt page images."""

    supplier_name: str = Field(description="Distributor name from header")
    remito_number: str | None = Field(default=None, description="Document number")
    date_issued: str | None = Field(
        default=None, description="Receipt date in ISO 8601 format"
    )
    page_count: int = Field(default=1, description="Number of pages detected")
    items: list[ExtractedLineItem] = Field(
        default_factory=list, description="Extracted line items"
    )
    fiscal_info: ExtractedFiscalInfo | None = None
    overall_confidence: int = Field(
        default=80, description="Extraction confidence 0-100"
    )
    extraction_notes: list[str] = Field(
        default_factory=list, description="Warnings or notes"
    )


class RemitoItemUpdate(BaseModel):
    """Payload for updating a staged remito line item."""

    product_id: int | None = None
    multiplier: int | None = None
    package_type: str | None = None
    target_unit_type: TargetUnitType | None = None
    effective_quantity: int | None = None
    is_verified_by_user: bool | None = None


class RemitoItemResponse(BaseModel):
    """DTO for a remito line item in API responses."""

    id: int
    remito_id: int
    line_index: int
    raw_description: str
    extracted_quantity: int
    extracted_unit_cost: int
    extracted_line_total: int
    product_id: int | None = None
    package_type: str | None = None
    multiplier: int
    target_unit_type: TargetUnitType
    effective_quantity: int
    quantity_to_commit: int
    calculated_unit_cost: int
    match_confidence: int
    match_strategy: MatchStrategy
    is_verified_by_user: bool


class RemitoResponse(BaseModel):
    """DTO for a complete remito header and item list."""

    id: int
    remito_number: str | None = None
    supplier_name: str
    date_issued: datetime | None = None
    status: RemitoStatus
    image_paths: str | None = None
    page_count: int
    fiscal_blanco_bps: int
    fiscal_negro_bps: int
    iva_rate_bps: int
    total_raw_amount: int
    total_real_amount: int
    notes: str | None = None
    created_at: datetime
    committed_at: datetime | None = None
    items: list[RemitoItemResponse] = Field(default_factory=list)


class SupplierMappingResponse(BaseModel):
    """DTO for a supplier-to-product mapping in the alias dictionary."""

    id: int
    supplier_name: str
    raw_item_pattern: str
    product_id: int
    package_type: str | None = None
    multiplier: int
    target_unit_type: TargetUnitType
    times_used: int
    last_matched_at: datetime
    created_at: datetime
