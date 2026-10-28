from pydantic import BaseModel, Field


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
