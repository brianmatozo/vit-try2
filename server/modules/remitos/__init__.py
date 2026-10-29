"""Remito ingestion and automated stock inbound vertical slice."""

from server.modules.remitos.audit import validate_line_totals
from server.modules.remitos.client import extract_remito
from server.modules.remitos.converter import PackageParseResult, parse_packaging
from server.modules.remitos.fiscal import FiscalCostResult, compute_unit_cost
from server.modules.remitos.models import (
    MatchStrategy,
    Remito,
    RemitoItem,
    RemitoStatus,
    SupplierProductMapping,
    TargetUnitType,
)
from server.modules.remitos.router import router
from server.modules.remitos.schemas import (
    ExtractedFiscalInfo,
    ExtractedLineItem,
    RemitoItemResponse,
    RemitoItemUpdate,
    RemitoResponse,
    RemitoVisionOutput,
    SupplierMappingResponse,
)

__all__ = [
    "ExtractedFiscalInfo",
    "ExtractedLineItem",
    "FiscalCostResult",
    "MatchStrategy",
    "PackageParseResult",
    "Remito",
    "RemitoItem",
    "RemitoItemResponse",
    "RemitoItemUpdate",
    "RemitoResponse",
    "RemitoStatus",
    "RemitoVisionOutput",
    "SupplierMappingResponse",
    "SupplierProductMapping",
    "TargetUnitType",
    "compute_unit_cost",
    "extract_remito",
    "parse_packaging",
    "router",
    "validate_line_totals",
]
