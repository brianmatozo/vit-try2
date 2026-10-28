"""Remito ingestion and automated stock inbound vertical slice."""

from server.modules.remitos.client import extract_remito
from server.modules.remitos.converter import PackageParseResult, parse_packaging
from server.modules.remitos.fiscal import FiscalCostResult, compute_unit_cost
from server.modules.remitos.schemas import (
    ExtractedFiscalInfo,
    ExtractedLineItem,
    RemitoVisionOutput,
)

__all__ = [
    "ExtractedFiscalInfo",
    "ExtractedLineItem",
    "FiscalCostResult",
    "PackageParseResult",
    "RemitoVisionOutput",
    "compute_unit_cost",
    "extract_remito",
    "parse_packaging",
]
