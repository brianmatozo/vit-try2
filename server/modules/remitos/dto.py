from datetime import datetime

from pydantic import BaseModel, Field

from server.modules.remitos.models import (
    MatchStrategy,
    RemitoStatus,
    TargetUnitType,
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
    overall_confidence: int | None = None
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


class RemitoConfigDTO(BaseModel):
    """Runtime configuration status for the OpenRouter vision client."""

    has_api_key: bool
    primary_model: str
    fallback_model: str


class RemitoConfigUpdate(BaseModel):
    """Payload to update runtime OpenRouter vision settings."""

    api_key: str | None = None
    primary_model: str | None = None


class ScanImagesRequest(BaseModel):
    """Payload for uploading receipt images and triggering vision extraction."""

    images: list[str] = Field(
        default_factory=list, description="Base64 data URIs of receipt pages"
    )
    model: str | None = None
    api_key: str | None = None
    blanco_pct: int = 60
    negro_pct: int = 40
    iva_pct: int = 21
    supplier_name: str | None = None
    mock: bool = False


class RemitoHeaderUpdate(BaseModel):
    """Payload for updating remito header-level settings."""

    fiscal_blanco_pct: int | None = None
    fiscal_negro_pct: int | None = None
    iva_pct: int | None = None
    notes: str | None = None
