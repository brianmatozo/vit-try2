from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class RemitoStatus(str, Enum):
    """Lifecycle state of an ingested delivery receipt."""

    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    STAGED = "staged"
    COMMITTED = "committed"
    REJECTED = "rejected"


class MatchStrategy(str, Enum):
    """How a remito line item was resolved to an internal Product."""

    EXACT_ALIAS = "exact_alias"
    FUZZY_CATALOG = "fuzzy_catalog"
    LLM_HEURISTIC = "llm_heuristic"
    MANUAL_OVERRIDE = "manual_override"
    UNMATCHED = "unmatched"


class TargetUnitType(str, Enum):
    """Whether conversion targets discrete units or bulk grams."""

    DISCRETE_UNIT = "discrete_unit"
    BULK_GRAMS = "bulk_grams"


class Remito(SQLModel, table=True):
    """Header record for an ingested supplier delivery receipt."""

    __tablename__ = "remitos"

    id: int | None = Field(default=None, primary_key=True)
    remito_number: str | None = Field(default=None, index=True)
    supplier_name: str = Field(index=True)
    date_issued: datetime | None = None
    status: RemitoStatus = Field(default=RemitoStatus.UPLOADED, index=True)
    image_paths: str | None = None
    page_count: int = 1
    raw_llm_payload: str | None = None

    # Fiscal parameters (stored as basis points: 6000 = 60.00%)
    fiscal_blanco_bps: int = Field(default=6000)
    fiscal_negro_bps: int = Field(default=4000)
    iva_rate_bps: int = Field(default=2100)

    # Document totals (whole ARS)
    total_raw_amount: int = Field(default=0)
    total_real_amount: int = Field(default=0)
    notes: str | None = None

    created_by_user_id: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    committed_at: datetime | None = None

    items: list["RemitoItem"] = Relationship(
        back_populates="remito",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        },
    )


class RemitoItem(SQLModel, table=True):
    """Single printed line item extracted from a delivery receipt."""

    __tablename__ = "remito_items"

    id: int | None = Field(default=None, primary_key=True)
    remito_id: int = Field(foreign_key="remitos.id", index=True)
    line_index: int
    raw_description: str
    extracted_quantity: int = Field(default=1)
    extracted_unit_cost: int = Field(default=0)
    extracted_line_total: int = Field(default=0)

    product_id: int | None = Field(default=None, foreign_key="products.id", index=True)
    package_type: str | None = None
    multiplier: int = Field(default=1)
    target_unit_type: TargetUnitType = Field(default=TargetUnitType.DISCRETE_UNIT)

    effective_quantity: int = Field(default=1)
    quantity_to_commit: int = Field(default=0)
    calculated_unit_cost: int = Field(default=0)
    match_confidence: int = Field(default=0)
    match_strategy: MatchStrategy = Field(default=MatchStrategy.UNMATCHED)
    is_verified_by_user: bool = Field(default=False)

    remito: Optional["Remito"] = Relationship(back_populates="items")


class SupplierProductMapping(SQLModel, table=True):
    """Cached mapping from raw supplier description to an internal Product."""

    __tablename__ = "supplier_product_mappings"

    id: int | None = Field(default=None, primary_key=True)
    supplier_name: str = Field(index=True)
    raw_item_pattern: str = Field(index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    package_type: str | None = None
    multiplier: int = Field(default=1)
    target_unit_type: TargetUnitType = Field(default=TargetUnitType.DISCRETE_UNIT)

    times_used: int = Field(default=1)
    last_matched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
