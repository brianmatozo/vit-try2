# Remito Ingestion & Automated Stock Inbound Service — Technical Specification

> **Version**: 1.1 · **Status**: Revised Draft (Modular 250 LOC & Phase 6 Governance Compliant) · **Last Updated**: 2026-10-27
>
> **Parent Specification**: [`SPECIFICATION.md`](../SPECIFICATION.md) (Vitalcer System Architecture)  
> **Governing Architecture & Refactoring Standards**:  
> - [`AGENTS.md`](../AGENTS.md) (Section 1.2: Zero Unconfirmed Paid API Calls; Section 6: Backend Architecture & Async SQLModel Contract; Section 6.B: The 250 LOC Backend Blueprint; Section 6.C: Async MVCC & Double-Entry Invariants; Section 6.E: Whole ARS Integer Currency)  
> - [`docs/backend_refactoring_plan.md`](backend_refactoring_plan.md) (Phase 6: Auxiliary Script Governance & Phase 3B Alignment)  
>
> **Scope**: End-to-end pipeline for ingesting physical Argentine delivery receipts (*Recibo X* / *Remitos*) via AI Vision, resolving wholesale packaging to internal single-unit SKUs, computing real net unit costs with Argentine fiscal splits, and committing audited stock through the existing double-entry inventory ledger.

---

## Table of Contents

1. [System Architecture & High-Level Flow](#1-system-architecture--high-level-flow)
   - [1.1 Problem Statement](#11-problem-statement)
   - [1.2 Solution Overview](#12-solution-overview)
   - [1.3 End-to-End Architecture Diagram](#13-end-to-end-architecture-diagram)
   - [1.4 Remito Lifecycle State Machine](#14-remito-lifecycle-state-machine)
   - [1.5 Vertical Domain Slice Architecture (`server/modules/remitos/`)](#15-vertical-domain-slice-architecture-servermodulesremitos)
   - [1.6 The 250 LOC Backend Blueprint & Domain Invariants](#16-the-250-loc-backend-blueprint--domain-invariants)
   - [1.7 Auxiliary Script Governance & Spike Decomposition (`spike_remito_vision.py`)](#17-auxiliary-script-governance--spike-decomposition-spike_remito_visionpy)
2. [Data Models & Database Schema](#2-data-models--database-schema)
3. [OpenRouter Vision Pipeline](#3-openrouter-vision-pipeline)
4. [Catalog Matching & Conversion Engine](#4-catalog-matching--conversion-engine)
5. [API Contract & Endpoints](#5-api-contract--endpoints)
6. [Staging UI Requirements](#6-staging-ui-requirements)
7. [Edge Cases, Failure Modes & Error Handling](#7-edge-cases-failure-modes--error-handling)
8. [Implementation Roadmap](#8-implementation-roadmap)

---

## 1. System Architecture & High-Level Flow

### 1.1 Problem Statement

Vitalcer's dietética receives daily deliveries from distributors (e.g. *New Day Distribuidora*, *Distribuidora Patagonia*, *La Natural*). Each delivery comes with a paper delivery note — an Argentine *Recibo X* or *Remito R* — listing wholesale packages, quantities, unit costs, and a proportional fiscal split between formally invoiced goods ("blanco" / con factura) and informally invoiced goods ("negro" / sin factura).

Today, stock receiving is a **manual, error-prone process**: the store manager opens the Admin Backoffice `/actions` page and types each product one-by-one into the "Recibir Stock" form. A single delivery from New Day can contain **30-60 line items**, making manual entry take 20-40 minutes and introducing data entry mistakes.

### 1.2 Solution Overview

Replace manual data entry with a **photo-first mobile ingestion workflow**:

1. **Snap** — Clerk photographs the multi-page paper remito on their phone.
2. **Extract** — An AI Vision pipeline (Gemini 2.0 Flash via OpenRouter) extracts clean structured printed data (descriptions, printed quantities, unit costs), explicitly ignoring handwritten ink marks to eliminate hallucinations.
3. **Match** — A multi-tier catalog matching engine resolves wholesale supplier descriptions to internal `Product` SKUs, applying packaging-to-unit conversion multipliers.
4. **Cost** — A fiscal split calculator computes the real landed unit cost per sellable item accounting for the blanco/negro split and IVA.
5. **Stage** — Results are persisted as a draft remito for clerk audit in a dedicated staging UI (with photo side-by-side for manual adjustment).
6. **Commit** — On clerk confirmation, an atomic transaction increments stock, updates `last_cost`, appends `InventoryLedger` entries, and caches supplier alias mappings for future auto-resolution.

### 1.3 End-to-End Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REMITO INGESTION PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────┘

  [Store Clerk Mobile / Tablet]
         │
         │ (1) Multi-page photo capture
         │     (JPEG/WebP, EXIF auto-rotated, ≤2048px max dimension)
         │
         ▼
  ┌──────────────────────────────────────────────┐
  │  FastAPI Backend                             │
  │  POST /api/v1/remitos/scan-and-stage         │
  │                                              │
  │  ┌────────────────────────────────────────┐  │
  │  │  (2) Image Preprocessor               │  │
  │  │  • EXIF orientation fix               │  │
  │  │  • Resize to ≤2048px                  │  │
  │  │  • Convert to base64 data URI         │  │
  │  │  • Multi-page correlation (Pag 1/2…)  │  │
  │  └────────────┬───────────────────────────┘  │
  │               │                              │
  │  ┌────────────▼───────────────────────────┐  │
  │  │  (3) OpenRouter Vision Client          │  │
  │  │  • Model: gemini-2.0-flash-001        │  │
  │  │  • Structured JSON output (Pydantic)  │  │
  │  │  • Printed-only extraction (clean)    │  │
  │  │  • Fallback: claude-3.5-sonnet        │  │
  │  └────────────┬───────────────────────────┘  │
  │               │                              │
  │  ┌────────────▼───────────────────────────┐  │
  │  │  (4) Catalog Matching Engine           │  │
  │  │  • Tier 1: Exact alias cache lookup   │  │
  │  │  • Tier 2: Trigram fuzzy matching      │  │
  │  │  • Tier 3: LLM heuristic fallback     │  │
  │  └────────────┬───────────────────────────┘  │
  │               │                              │
  │  ┌────────────▼───────────────────────────┐  │
  │  │  (5) Packaging Parser & Multiplier     │  │
  │  │  • Regex extraction: "x 10 u" → 10    │  │
  │  │  • Bulk weight conversion: "5 kg" → g  │  │
  │  │  • Package type classification         │  │
  │  └────────────┬───────────────────────────┘  │
  │               │                              │
  │  ┌────────────▼───────────────────────────┐  │
  │  │  (6) Fiscal Split & Cost Calculator    │  │
  │  │  • Blanco/Negro proportional split     │  │
  │  │  • IVA 21% on blanco portion           │  │
  │  │  • Real net unit cost (whole ARS)      │  │
  │  └────────────┬───────────────────────────┘  │
  │               │                              │
  │               ▼                              │
  │  ┌────────────────────────────────────────┐  │
  │  │  PostgreSQL                            │  │
  │  │  Saves: Remito (STAGED)               │  │
  │  │         RemitoItem rows               │  │
  │  │         raw_llm_payload (JSONB)        │  │
  │  └────────────────────────────────────────┘  │
  └──────────────────────────────────────────────┘
         │
         │ (7) Clerk reviews on Admin Staging Screen
         │     /remitos/:id
         │
         ▼
  ┌──────────────────────────────────────────────┐
  │  Admin Backoffice SPA (Svelte 5)             │
  │  • Side-by-side: photo ↔ data grid           │
  │  • Color-coded audit badges (🟢🟡🔴🟣)      │
  │  • Inline editing, manual product override    │
  │  • Fiscal split sliders (real-time recalc)    │
  └──────────────┬───────────────────────────────┘
         │
         │ (8) Clerk confirms
         │     POST /api/v1/remitos/:id/confirm
         │
         ▼
  ┌──────────────────────────────────────────────┐
  │  Double-Entry Commit Coordinator (Atomic Tx) │
  │  • SELECT FOR UPDATE on each Product         │
  │  • Product.current_stock += qty_to_commit    │
  │  • Product.last_cost = calculated_unit_cost  │
  │  • INSERT InventoryLedger (type=receiving)   │
  │  • UPSERT supplier_product_mappings          │
  │  • Remito.status = COMMITTED                 │
  └──────────────────────────────────────────────┘
```

### 1.4 Remito Lifecycle State Machine

```
  ┌──────────┐    scan-and-stage    ┌───────────┐    extracting    ┌────────────┐
  │ UPLOADED  │──────────────────►  │ EXTRACTING │──────────────►  │   STAGED   │
  └──────────┘                     └───────────┘                  └─────┬──────┘
                                                                        │
                                        ┌───────────────────────────────┤
                                        │                               │
                                        ▼                               ▼
                                  ┌───────────┐                  ┌────────────┐
                                  │ REJECTED  │                  │ COMMITTED  │
                                  └───────────┘                  └────────────┘
```

| State | Description | Transitions |
| :--- | :--- | :--- |
| `UPLOADED` | Images received, not yet processed | → `EXTRACTING` |
| `EXTRACTING` | Vision pipeline in progress | → `STAGED` (success) or `REJECTED` (total failure) |
| `STAGED` | Extraction complete, awaiting clerk review and confirmation | → `COMMITTED` or `REJECTED` |
| `COMMITTED` | Stock committed, ledger entries created, alias cache updated | Terminal |
| `REJECTED` | Clerk discarded this remito (duplicate, unreadable, etc.) | Terminal |

### 1.5 Vertical Domain Slice Architecture (`server/modules/remitos/`)

In compliance with [`AGENTS.md`](../AGENTS.md) Section 6.A and [`docs/backend_refactoring_plan.md`](backend_refactoring_plan.md) Phase 6, the Remito Ingestion service is implemented as a dedicated vertical domain slice under `server/modules/remitos/`. All legacy horizontal structures (`server/services/remito/`, `server/models/remito.py`, `server/schemas/remito.py`, `server/api/v1/endpoints/remitos.py`) are strictly prohibited.

```text
server/modules/remitos/
├── __init__.py           # Package exports & public API (< 15 LOC)
├── models.py             # SQLModel tables: Remito, RemitoItem, SupplierProductMapping (< 140 LOC)
├── schemas.py            # Pydantic extraction schemas and request/response DTOs (< 100 LOC)
├── client.py             # OpenRouter Vision client & image preprocessor (< 120 LOC)
├── converter.py          # Packaging parser & conversion multiplier detection (< 90 LOC)
├── fiscal.py             # 60/40 fiscal split calculator (blanco/negro + 21% IVA) (< 80 LOC)
├── matching.py           # 3-tier catalog resolution engine (alias → fuzzy → LLM) (< 120 LOC)
├── service.py            # Lifecycle orchestration, atomic receiving commit, alias caching (< 140 LOC)
└── router.py             # Thin HTTP coordinator mounted at /api/v1/remitos (< 130 LOC)
```

| Component | Module Path | LOC Ceiling | Responsibility |
| :--- | :--- | :--- | :--- |
| **Package Exports** | `server/modules/remitos/__init__.py` | < 15 LOC | Module exports (`router`, `Remito`, `RemitoItem`, etc.) |
| **SQLModel Models** | `server/modules/remitos/models.py` | < 140 LOC | `Remito`, `RemitoItem`, `SupplierProductMapping` table definitions |
| **Pydantic Schemas** | `server/modules/remitos/schemas.py` | < 100 LOC | Vision extraction schemas and API request/response DTOs |
| **Vision Client & Preprocessor** | `server/modules/remitos/client.py` | < 120 LOC | OpenRouter async client, EXIF orientation fix, WebP downscaling, system prompt |
| **Packaging Converter** | `server/modules/remitos/converter.py` | < 90 LOC | Regex multiplier extraction, packaging classification, unit normalization |
| **Fiscal Calculator** | `server/modules/remitos/fiscal.py` | < 80 LOC | 60/40 fiscal split arithmetic, IVA on blanco, integer ARS unit cost math |
| **Catalog Matcher** | `server/modules/remitos/matching.py` | < 120 LOC | 3-tier product resolution (Tier 1 alias → Tier 2 trigram → Tier 3 LLM) |
| **Remito Service Engine** | `server/modules/remitos/service.py` | < 140 LOC | Inbound receiving orchestrator, double-entry stock commit, alias cache upsert |
| **API Router** | `server/modules/remitos/router.py` | < 130 LOC | Thin HTTP coordinator delegating to `service.py`, global exception integration |

### 1.6 The 250 LOC Backend Blueprint & Domain Invariants

Per [`AGENTS.md`](../AGENTS.md) Section 6.B and Section 6.C, the remito domain enforces strict architectural invariants:

1. **Strict 250 LOC Ceiling**: No single Python file under `server/modules/remitos/` may exceed 250 LOC. The modular structure targets a post-refactor profile of **< 140 LOC** per file, leaving ample headroom for future business requirements.
2. **Thin HTTP Routers**: `router.py` performs zero business logic, raw SQL queries, or manual try/except blocks. It handles HTTP parameter validation, calls `service.py`, and returns Pydantic response models.
3. **Decoupled Cross-Slice Relationships**: Models never import tables directly from `server/modules/catalog/models.py`. Foreign keys use table string names (e.g., `foreign_key="products.id"`). Relationships use string forward references with `if TYPE_CHECKING:` guards. All models are registered centrally in `server/core/models_registry.py`.
4. **Explicit Aggregate Routing**: The router is explicitly mounted in `server/api/v1/router.py`:
   ```python
   from server.modules.remitos.router import router as remitos_router

   v1_router.include_router(remitos_router)
   ```
5. **Centralized Domain Exceptions**: Endpoints eliminate repetitive `try...except` blocks, throwing typed domain exceptions (`EntityNotFoundError`, `InvalidMovementError`, `VitalcerException`) registered in `server/core/exceptions.py`. Custom handlers strictly emit `{"detail": exc.message}` to preserve OpenAPI and frontend toast contract consistency.
6. **Append-Only Double-Entry Receiving**: Stock commits never overwrite balances directly. On confirmation, `service.py` executes an atomic transaction locking each product via `select(Product).options(noload("*")).where(Product.id == pid).with_for_update()` and appending an immutable `InventoryLedger` entry with `movement_type = "receiving"`.
7. **Whole ARS Integer Currency**: All extracted wholesale costs, calculated landed pack costs, unit prices, and IVA figures are strictly stored and computed as whole Argentine Pesos (`int`), using integer arithmetic or explicit banker's rounding (`round()`).

### 1.7 Auxiliary Script Governance & Spike Decomposition (`spike_remito_vision.py`)

During initial research and Phase 3B prototyping, an exploratory spike script [`scripts/spike_remito_vision.py`](file:///home/brian/dev/scripts/spike_remito_vision.py) (906 LOC) was authored to evaluate Gemini 2.0 Flash vision extraction against physical Argentine remito photos.

#### Auxiliary Script Governance Policy
In accordance with [`docs/backend_refactoring_plan.md`](backend_refactoring_plan.md) Phase 6:
* **Standalone Classification**: `scripts/spike_remito_vision.py` is explicitly tagged with an architecture header as an auxiliary research prototype.
* **Zero Runtime Server Import**: This script is strictly forbidden from being imported by or executed within `server/`. It operates solely as a developer CLI tool.
* **Zero Autonomous Paid API Calls**: In accordance with [`AGENTS.md`](../AGENTS.md) Section 1.2, AI agents and automated CI test runners must **never** execute live billable API calls using user credentials. All test suites and automated benchmarks must run against `--mock` mode or offline JSON fixtures stored in `tests/fixtures/remitos/`.

#### Productionization Decomposition Matrix
The 906 LOC monolithic spike is systematically decomposed into the vertical domain slice `server/modules/remitos/`:

| Spike Source Range (`spike_remito_vision.py`) | Target Modular Component | Target LOC | Responsibilities Migrated |
| :--- | :--- | :--- | :--- |
| **Lines 1–120** | `scripts/spike_remito_vision.py` | Retained (CLI) | Standalone developer CLI, Argparse runner, Rich terminal rendering |
| **Lines 121–220** | `server/modules/remitos/schemas.py` | < 100 LOC | `ExtractedLineItem`, `ExtractedFiscalInfo`, `RemitoVisionOutput`, API DTOs |
| **Lines 221–350** | `server/modules/remitos/client.py` | < 120 LOC | PIL image preprocessing: EXIF transposition, WebP conversion, resize to ≤2048px |
| **Lines 351–500** | `server/modules/remitos/client.py` | < 120 LOC | OpenRouter async client, system prompt, Gemini 2.0 Flash call & Sonnet retry |
| **Lines 501–650** | `server/modules/remitos/converter.py` | < 90 LOC | Regex packaging multiplier detection (`x 10 u`, `pack de 6`, `kg`, etc.) |
| **Lines 651–750** | `server/modules/remitos/fiscal.py` | < 80 LOC | 60/40 fiscal split, basis points calculations (6000 bps / 4000 bps / 2100 bps) |
| **Lines 751–850** | `server/modules/remitos/matching.py` | < 120 LOC | Supplier text normalization, Tier 1 alias lookup, Tier 2 trigram, Tier 3 LLM |
| **Lines 851–906** | `server/modules/remitos/service.py` & `models.py` | < 140 LOC each | Database persistence, staged state management, atomic stock receiving commit |

---

## 2. Data Models & Database Schema

All new tables follow Vitalcer's existing conventions:
- **Integer whole ARS** for all monetary values (no centavos — [Currency Invariant](../AGENTS.md)).
- **Append-only `InventoryLedger`** for stock mutations (no direct `UPDATE products SET current_stock`).
- **`SQLModel`** with `table=True` for PostgreSQL DDL and Python ORM.
- **UTC timestamps** via `datetime.now(timezone.utc)`.

### 2.1 `remitos` Table

Stores the header-level data for each ingested delivery receipt.

```python
# server/modules/remitos/models.py

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from server.modules.remitos.models import RemitoItem


class RemitoStatus(str, Enum):
    """Lifecycle state of an ingested delivery receipt."""

    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    STAGED = "staged"
    COMMITTED = "committed"
    REJECTED = "rejected"


class Remito(SQLModel, table=True):
    """Header record for an ingested supplier delivery receipt (Remito / Recibo X)."""

    __tablename__ = "remitos"

    id: int | None = Field(default=None, primary_key=True)

    # --- Supplier & Document Identity ---
    remito_number: str | None = Field(
        default=None,
        index=True,
        description="Supplier's delivery note number (e.g. '0001-00045231')",
    )
    supplier_name: str = Field(
        index=True,
        description="Distributor name (e.g. 'New Day Distribuidora')",
    )
    date_issued: datetime | None = Field(
        default=None,
        description="Date printed on the physical delivery receipt",
    )

    # --- Status ---
    status: RemitoStatus = Field(
        default=RemitoStatus.UPLOADED,
        index=True,
    )

    # --- Image Storage ---
    # JSON array of relative paths or URLs to stored receipt photos
    # e.g. ["remitos/2026-10-09/img_001.webp", "remitos/2026-10-09/img_002.webp"]
    image_paths: str | None = Field(
        default=None,
        description="JSON array of stored receipt image paths",
    )
    page_count: int = Field(default=1)

    # --- Raw LLM Output (Audit Trail) ---
    raw_llm_payload: str | None = Field(
        default=None,
        description="Full JSON response from Vision LLM, stored for auditability",
    )

    # --- Fiscal Split Parameters ---
    # Stored as basis points (integer): 6000 = 60.00%
    # Using basis points avoids floating-point and respects integer-only invariant
    fiscal_blanco_bps: int = Field(
        default=6000,
        description="Formal invoice fraction in basis points (6000 = 60%)",
    )
    fiscal_negro_bps: int = Field(
        default=4000,
        description="Informal fraction in basis points (4000 = 40%)",
    )
    iva_rate_bps: int = Field(
        default=2100,
        description="IVA rate in basis points (2100 = 21%)",
    )

    # --- Document Totals (whole ARS) ---
    total_raw_amount: int = Field(
        default=0,
        description="Sum of raw line totals as printed on receipt (whole ARS)",
    )
    total_real_amount: int = Field(
        default=0,
        description="Total after fiscal split & IVA computation (whole ARS)",
    )

    # --- Metadata ---
    notes: str | None = None
    created_by_user_id: int | None = Field(
        default=None,
        foreign_key="users.id",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    committed_at: datetime | None = Field(default=None)

    # --- Relationships ---
    items: list["RemitoItem"] = Relationship(
        back_populates="remito",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        },
    )
```

**Design Decisions**:
- **Basis points** for fiscal ratios (`fiscal_blanco_bps`, `fiscal_negro_bps`, `iva_rate_bps`) instead of floats. This keeps all storage as integers, consistent with the whole-ARS currency invariant, while providing 0.01% granularity. `6000 bps = 60.00%`.
- **`raw_llm_payload`** stored as a JSON text column for full audit traceability of what the vision model returned, enabling post-hoc accuracy analysis and prompt improvement.
- **`image_paths`** stored as a JSON-serialized string array rather than a separate `remito_images` table — sufficient for 1-4 page receipts without join overhead.

### 2.2 `remito_items` Table

Each line item extracted from the delivery receipt, with catalog matching and cost computation results.

```python
```python
class MatchStrategy(str, Enum):
    """How a remito line item was resolved to an internal Product."""

    EXACT_ALIAS = "exact_alias"  # Cached supplier_product_mapping hit
    FUZZY_CATALOG = "fuzzy_catalog"  # Trigram/Levenshtein similarity match
    LLM_HEURISTIC = "llm_heuristic"  # Vision model suggested mapping
    MANUAL_OVERRIDE = "manual_override"  # Clerk manually selected product
    UNMATCHED = "unmatched"  # No resolution found


class TargetUnitType(str, Enum):
    """Whether the conversion target is discrete units or bulk grams."""

    DISCRETE_UNIT = "discrete_unit"
    BULK_GRAMS = "bulk_grams"


class RemitoItem(SQLModel, table=True):
    """Single printed line item extracted from a delivery receipt with matching & cost data."""

    __tablename__ = "remito_items"

    id: int | None = Field(default=None, primary_key=True)
    remito_id: int = Field(foreign_key="remitos.id", index=True)
    line_index: int = Field(
        description="Sequential line position in the original document (0-based)",
    )

    # --- Raw Extraction (as printed on receipt) ---
    raw_description: str = Field(
        description="Full text extracted by Vision LLM "
        "(e.g. 'Barritas Almendra x 41 gr x 10 u (Integra)')",
    )
    extracted_quantity: int = Field(
        default=1,
        description="Number of wholesale packages as printed on receipt",
    )
    extracted_unit_cost: int = Field(
        default=0,
        description="Cost per wholesale package as printed (whole ARS)",
    )
    extracted_line_total: int = Field(
        default=0,
        description="Line total as printed on receipt (whole ARS)",
    )

    # --- Catalog Matching & Packaging Conversion ---
    product_id: int | None = Field(
        default=None,
        foreign_key="products.id",
        index=True,
        description="Matched internal Product ID (null if unmatched)",
    )
    package_type: str | None = Field(
        default=None,
        description="Detected wholesale packaging type "
        "(caja, pack, bolsa, display, unidad, kg, etc.)",
    )
    multiplier: int = Field(
        default=1,
        description="Conversion multiplier: sellable units per wholesale package "
        "(e.g. 10 for a box of 10 bars, or 1000 for a 1kg bulk bag → grams)",
    )
    target_unit_type: TargetUnitType = Field(
        default=TargetUnitType.DISCRETE_UNIT,
    )

    # --- Computed Commit Values ---
    effective_quantity: int = Field(
        default=1,
        description="Final package count to receive (defaults to extracted_quantity; "
        "editable by clerk in staging UI)",
    )
    quantity_to_commit: int = Field(
        default=0,
        description="Total sellable units/grams to add to stock "
        "(= effective_quantity × multiplier)",
    )
    calculated_unit_cost: int = Field(
        default=0,
        description="Real net cost per sellable unit/reference weight after fiscal split "
        "(whole ARS)",
    )

    # --- Match Confidence ---
    match_confidence: int = Field(
        default=0,
        description="Matching confidence as percentage 0-100",
    )
    match_strategy: MatchStrategy = Field(
        default=MatchStrategy.UNMATCHED,
    )
    is_verified_by_user: bool = Field(default=False)

    # --- Relationships ---
    remito: Optional["Remito"] = Relationship(back_populates="items")
```

**Key Design Notes**:

- **`effective_quantity`**: Defaults to `extracted_quantity` from the printed document. If an item physically didn't arrive or arrived in different quantity, the clerk edits this field directly on the staging screen (or sets to `0` to exclude).
- **`quantity_to_commit`**: Pre-computed as `effective_quantity × multiplier`, ready for direct use in `receive_stock`.
- **`match_confidence`**: Integer 0-100 (not a float) — consistent with whole-number storage. 100 = exact alias cache hit, 75+ = strong fuzzy match, <50 = LLM suggestion.

### 2.3 `supplier_product_mappings` Table (Alias Cache)

Caches the clerk-verified association between a supplier's raw item description and an internal `Product`, so that subsequent remitos with the same text are resolved automatically.

```python
class SupplierProductMapping(SQLModel, table=True):
    """Cached mapping from a supplier's raw item text to an internal Product & multiplier.

    Once a clerk confirms a mapping, subsequent remitos containing the same
    (supplier_name, normalized_pattern) resolve instantly via Tier 1 exact lookup.
    """

    __tablename__ = "supplier_product_mappings"

    id: int | None = Field(default=None, primary_key=True)

    supplier_name: str = Field(
        index=True,
        description="Normalized distributor name (lowercased, trimmed)",
    )
    raw_item_pattern: str = Field(
        index=True,
        description="Normalized raw item description from supplier receipt "
        "(lowercased, whitespace-collapsed, punctuation-stripped)",
    )
    product_id: int = Field(
        foreign_key="products.id",
        index=True,
        description="Internal Product this supplier text maps to",
    )
    package_type: str | None = Field(default=None)
    multiplier: int = Field(
        default=1,
        description="Sellable units per wholesale package (e.g. 10 for a 10-pack)",
    )
    target_unit_type: TargetUnitType = Field(
        default=TargetUnitType.DISCRETE_UNIT,
    )

    # --- Usage Statistics ---
    times_used: int = Field(default=1)
    last_matched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # Unique constraint: one mapping per (supplier, normalized description)
    __table_args__ = (
        # UniqueConstraint added via sa_column_kwargs or Alembic migration
    )
```

**Normalization Algorithm** for `raw_item_pattern`:
```python
import re
import unicodedata


def normalize_supplier_text(raw: str) -> str:
    """Normalize supplier item text for deterministic alias cache lookups.

    Steps:
    1. Unicode NFKD decomposition + strip diacritics (á→a, ñ→n)
    2. Lowercase
    3. Collapse whitespace
    4. Strip punctuation except 'x' multiplier markers
    5. Remove common noise words (promo, oferta, liq, desc)
    """
    # Strip accents
    text = unicodedata.normalize("NFKD", raw)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove noise punctuation but keep 'x' multiplier syntax
    text = re.sub(r"[()[\]{}\-–—/\\|.,;:!?\"'`]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Remove common noise words
    noise = {"promo", "oferta", "liq", "liquidacion", "desc", "descuento", "nuevo"}
    tokens = [t for t in text.split() if t not in noise]
    return " ".join(tokens)
```

### 2.4 `Product` Model Extension

A single new nullable column is added to the existing `Product` model in the catalog slice:

```python
# server/modules/catalog/models.py — addition

    # Cost tracking (updated on remito commit)
    last_cost: int | None = Field(
        default=None,
        description="Last known supplier cost per sellable unit in whole ARS. "
        "Updated on remito commit. Null if never received via remito.",
    )
```

This records the most recent real landed cost per discrete unit (or per `bulk_reference_grams` for bulk products), enabling future margin analysis and pricing decisions. Stored in **whole ARS** per the system-wide currency invariant.

### 2.5 Central Registry Registration (`models_registry.py`)

To prevent circular imports and guarantee that all SQLModel metadata and mapper relationships resolve in deterministic order across slices:

```python
# server/core/models_registry.py — addition
import server.modules.catalog.models  # noqa: F401
import server.modules.identity.models  # noqa: F401
import server.modules.inventory.models  # noqa: F401
import server.modules.remitos.models  # noqa: F401
```

Foreign keys between slices use string references (`foreign_key="products.id"`). Relationships use forward string references (`"Product"`, `"RemitoItem"`) guarded by `if TYPE_CHECKING:` blocks, preserving complete cross-slice decoupling.

### 2.6 PostgreSQL DDL Summary

```sql
-- Remitos header table
CREATE TABLE remitos (
    id              SERIAL PRIMARY KEY,
    remito_number   VARCHAR(64),
    supplier_name   VARCHAR(255) NOT NULL,
    date_issued     TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'uploaded',
    image_paths     TEXT,           -- JSON array
    page_count      INTEGER NOT NULL DEFAULT 1,
    raw_llm_payload TEXT,           -- Full JSON response
    fiscal_blanco_bps INTEGER NOT NULL DEFAULT 6000,
    fiscal_negro_bps  INTEGER NOT NULL DEFAULT 4000,
    iva_rate_bps      INTEGER NOT NULL DEFAULT 2100,
    total_raw_amount  INTEGER NOT NULL DEFAULT 0,
    total_real_amount INTEGER NOT NULL DEFAULT 0,
    notes             TEXT,
    created_by_user_id INTEGER REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    committed_at    TIMESTAMPTZ
);
CREATE INDEX ix_remitos_supplier_name ON remitos(supplier_name);
CREATE INDEX ix_remitos_status ON remitos(status);
CREATE INDEX ix_remitos_remito_number ON remitos(remito_number);

-- Remito line items
CREATE TABLE remito_items (
    id                    SERIAL PRIMARY KEY,
    remito_id             INTEGER NOT NULL REFERENCES remitos(id) ON DELETE CASCADE,
    line_index            INTEGER NOT NULL,
    raw_description       TEXT NOT NULL,
    extracted_quantity    INTEGER NOT NULL DEFAULT 1,
    extracted_unit_cost   INTEGER NOT NULL DEFAULT 0,
    extracted_line_total  INTEGER NOT NULL DEFAULT 0,
    product_id            INTEGER REFERENCES products(id),
    package_type          VARCHAR(32),
    multiplier            INTEGER NOT NULL DEFAULT 1,
    target_unit_type      VARCHAR(20) NOT NULL DEFAULT 'discrete_unit',
    effective_quantity    INTEGER NOT NULL DEFAULT 1,
    quantity_to_commit    INTEGER NOT NULL DEFAULT 0,
    calculated_unit_cost  INTEGER NOT NULL DEFAULT 0,
    match_confidence      INTEGER NOT NULL DEFAULT 0,
    match_strategy        VARCHAR(20) NOT NULL DEFAULT 'unmatched',
    is_verified_by_user   BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX ix_remito_items_remito_id ON remito_items(remito_id);
CREATE INDEX ix_remito_items_product_id ON remito_items(product_id);

-- Supplier product alias cache
CREATE TABLE supplier_product_mappings (
    id               SERIAL PRIMARY KEY,
    supplier_name    VARCHAR(255) NOT NULL,
    raw_item_pattern TEXT NOT NULL,
    product_id       INTEGER NOT NULL REFERENCES products(id),
    package_type     VARCHAR(32),
    multiplier       INTEGER NOT NULL DEFAULT 1,
    target_unit_type VARCHAR(20) NOT NULL DEFAULT 'discrete_unit',
    times_used       INTEGER NOT NULL DEFAULT 1,
    last_matched_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(supplier_name, raw_item_pattern)
);
CREATE INDEX ix_spm_supplier ON supplier_product_mappings(supplier_name);
CREATE INDEX ix_spm_product ON supplier_product_mappings(product_id);

-- Product extension
ALTER TABLE products ADD COLUMN last_cost INTEGER;
```

### 2.7 Entity Relationship Diagram

```
┌──────────┐       ┌──────────────┐       ┌──────────┐
│  users   │       │   remitos    │       │ products │
│──────────│       │──────────────│       │──────────│
│ id (PK)  │◄──────│ created_by…  │       │ id (PK)  │
└──────────┘       │ id (PK)      │       │ last_cost│ ← NEW
                   │ supplier_name│       └─────┬────┘
                   │ status       │             │
                   │ fiscal_*_bps │             │
                   └──────┬───────┘             │
                          │ 1:N                 │
                   ┌──────▼───────┐             │
                   │ remito_items │             │
                   │──────────────│             │
                   │ id (PK)      │             │
                   │ remito_id FK │             │
                   │ product_id FK├─────────────┘
                   │ multiplier   │             │
                   │ qty_to_commit│             │
                   └──────────────┘             │
                                                │
                   ┌─────────────────────────┐  │
                   │ supplier_product_mappings│  │
                   │─────────────────────────│  │
                   │ supplier_name           │  │
                   │ raw_item_pattern        │  │
                   │ product_id FK           ├──┘
                   │ multiplier              │
                   │ UNIQUE(supplier, pattern)│
                   └─────────────────────────┘

                   ┌──────────────────┐
                   │ inventory_ledger │  ← EXISTING (unchanged)
                   │──────────────────│
                   │ product_id FK    │
                   │ movement_type    │  "receiving"
                   │ quantity_delta   │
                   │ balance_after    │
                   │ reference_id     │  "REMITO-{remito.id}"
                   └──────────────────┘
```

---

## 3. OpenRouter Vision Pipeline

### 3.1 Model Selection & Rationale

| Model | Role | Cost (Input / Output per 1M tokens) | Speed | Strengths |
| :--- | :--- | :--- | :--- | :--- |
| **`google/gemini-2.0-flash-001`** | Primary workhorse | ~$0.10 / $0.40 | < 3s for 2-page batch | Natively multimodal, excellent Spanish OCR, structured JSON output, massive context window (1M tokens). Best cost-speed-accuracy tradeoff for printed Argentine receipts. |
| **`anthropic/claude-3.5-sonnet`** | Fallback for difficult scans | ~$3.00 / $15.00 | 5-10s | Superior reasoning on low-contrast dot-matrix print, chaotic overlapping handwriting, and water-damaged paper. 30x more expensive — use only on retry after Gemini confidence < 50%. |

**Decision**: Gemini 2.0 Flash handles ~95% of delivery notes. Automatic fallback to Sonnet when the Gemini response has a `"low_confidence": true` flag or fails structured output validation.

### 3.2 API Integration Blueprint (`server/modules/remitos/client.py` — < 120 LOC)

The Vision client consolidates both image preprocessing (EXIF transposition, WebP downscaling) and OpenRouter async requests within a single cohesive module under **120 LOC**:

```python
# server/modules/remitos/client.py

from openai import AsyncOpenAI
from server.core.config import settings

# OpenRouter via OpenAI-compatible SDK
_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
    default_headers={
        "HTTP-Referer": "https://vitalcer.app",
        "X-Title": "Vitalcer Remito Ingestion",
    },
)

PRIMARY_MODEL = "google/gemini-2.0-flash-001"
FALLBACK_MODEL = "anthropic/claude-3.5-sonnet"
```

> [!IMPORTANT]
> **Zero Billable API Calls Invariant**: In accordance with [`AGENTS.md`](../AGENTS.md) Section 1.2 and Section 4.8, live network calls to OpenRouter are strictly forbidden during automated unit and integration tests. Test suites inject pre-recorded JSON fixture responses (`tests/fixtures/remitos/`) or mock the OpenRouter client completion method directly.

**Image Preprocessing** (before sending to OpenRouter):

```python
# server/modules/remitos/client.py — image preprocessing helper

from PIL import Image, ImageOps
import base64
import io

MAX_DIMENSION = 2048  # Cap for token efficiency
QUALITY = 85


async def preprocess_image(raw_bytes: bytes) -> str:
    """Fix EXIF orientation, resize, and encode to base64 data URI.

    Returns: "data:image/webp;base64,<encoded>" string ready for
    OpenAI vision API content blocks.
    """
    img = Image.open(io.BytesIO(raw_bytes))

    # Auto-fix EXIF rotation (phone camera orientation metadata)
    img = ImageOps.exif_transpose(img)

    # Downscale if larger than 2048px on longest side
    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

    # Convert to WebP for optimal token/byte ratio
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=QUALITY)
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{b64}"
```

### 3.3 System Prompt & Structured Output Schema

**System Prompt** (sent with every vision request):

```python
REMITO_EXTRACTION_SYSTEM_PROMPT = """\
You are an expert data extraction system specialized in Argentine commercial \
delivery receipts (Remitos, Recibos X, Liquidaciones) from food and dietary \
product distributors (dietéticas).

TASK: Extract structured data from the provided receipt photo(s).

CRITICAL CONTEXT:
- These are WHOLESALE delivery notes, not retail receipts.
- Items are listed as wholesale packages (cajas, packs, bolsas, displays).
- Prices are in Argentine Pesos (ARS), integer amounts (no centavos).
- Receipts may span multiple pages (e.g. "Pag 1/2" and "Pag 2/2").

CRITICAL EXTRACTION RULE — IGNORE HANDWRITING:
- Focus EXCLUSIVELY on extracting the original PRINTED text of the receipt.
- Completely IGNORE all handwritten pen marks, blue/black ballpoint ink, checkmarks,
  ticks, crossed-out lines, or handwritten notes. Do NOT attempt to detect or read handwriting.
- Extract the printed descriptions, quantities, and prices as originally printed.
- If a printed line is partially illegible, extract what you can with lower confidence.
- All monetary values must be integers (whole ARS, no decimals).

OUTPUT: Return a single JSON object matching the provided schema exactly. \
Do not include any text outside the JSON object.\
"""
```

**Pydantic Output Schemas** (used for structured JSON mode):

```python
# server/modules/remitos/schemas.py — Vision output models

from pydantic import BaseModel, Field


class ExtractedLineItem(BaseModel):
    """Single printed line item extracted from the delivery receipt by Vision."""

    line_index: int = Field(description="0-based line position")
    raw_description: str = Field(
        description="Full item description as printed "
        "(e.g. 'Barritas Almendra x 41 gr x 10 u (Integra)')",
    )
    quantity: int = Field(
        default=1,
        description="Number of wholesale packages (as printed)",
    )
    unit_cost: int = Field(
        default=0,
        description="Cost per package in whole ARS (as printed)",
    )
    line_total: int = Field(
        default=0,
        description="Line total in whole ARS (as printed)",
    )
    confidence: int = Field(
        default=90,
        description="Extraction confidence 0-100",
    )


class ExtractedFiscalInfo(BaseModel):
    """Fiscal split and total information from receipt header/footer."""

    subtotal: int | None = Field(
        default=None,
        description="Subtotal before tax/split (whole ARS)",
    )
    total: int | None = Field(
        default=None,
        description="Document total (whole ARS)",
    )
    discount_percentage: int | None = Field(
        default=None,
        description="Global discount percentage if printed (0-100)",
    )
    blanco_percentage: int | None = Field(
        default=None,
        description="Percentage billed formally 'con factura' (e.g. 60)",
    )
    negro_percentage: int | None = Field(
        default=None,
        description="Percentage billed informally 'sin factura' (e.g. 40)",
    )
    iva_percentage: int | None = Field(
        default=None,
        description="IVA rate printed on receipt (e.g. 21)",
    )


class RemitoVisionOutput(BaseModel):
    """Complete structured extraction from one or more receipt page images."""

    supplier_name: str = Field(
        description="Distributor / supplier name from receipt header",
    )
    remito_number: str | None = Field(
        default=None,
        description="Document number (e.g. '0001-00045231')",
    )
    date_issued: str | None = Field(
        default=None,
        description="Receipt date in ISO 8601 format (YYYY-MM-DD) if legible",
    )
    page_count: int = Field(
        default=1,
        description="Number of pages detected",
    )
    items: list[ExtractedLineItem] = Field(
        description="All extracted line items (including crossed-out)",
    )
    fiscal_info: ExtractedFiscalInfo | None = Field(default=None)
    overall_confidence: int = Field(
        default=80,
        description="Overall extraction confidence 0-100",
    )
    extraction_notes: list[str] = Field(
        default_factory=list,
        description="Any warnings or notes about extraction quality",
    )
```

### 3.4 Vision Request Construction

```python
async def extract_remito(
    image_data_uris: list[str],
    model: str = PRIMARY_MODEL,
) -> RemitoVisionOutput:
    """Send receipt image(s) to OpenRouter and parse structured extraction.

    Args:
        image_data_uris: List of base64 data URIs (one per page).
        model: OpenRouter model identifier.

    Returns:
        Validated RemitoVisionOutput with all extracted line items.

    Raises:
        VisionExtractionError: On parse failure or low confidence.
    """
    # Build multi-image content blocks
    content_blocks: list[dict] = []
    for i, uri in enumerate(image_data_uris):
        if len(image_data_uris) > 1:
            content_blocks.append(
                {
                    "type": "text",
                    "text": f"--- Receipt Page {i + 1} of {len(image_data_uris)} ---",
                }
            )
        content_blocks.append(
            {
                "type": "image_url",
                "image_url": {"url": uri},
            }
        )

    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": REMITO_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": content_blocks},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,  # Near-deterministic for structured extraction
        max_tokens=4096,
    )

    raw_json = response.choices[0].message.content
    result = RemitoVisionOutput.model_validate_json(raw_json)

    # Auto-fallback: if overall confidence is too low, retry with Sonnet
    if result.overall_confidence < 50 and model == PRIMARY_MODEL:
        return await extract_remito(image_data_uris, model=FALLBACK_MODEL)

    return result
```

---

## 4. Catalog Matching & Conversion Engine

### 4.1 Three-Tier Matching Algorithm

```
  Raw Description from Vision
  "Barritas Almendra x 41 gr x 10 u (Integra)"
         │
         ▼
  ┌──────────────────────────────┐
  │  Tier 1: EXACT ALIAS CACHE  │   ← O(1) lookup in supplier_product_mappings
  │  normalize(text) → mapping  │      by (supplier_name, normalized_pattern)
  │  Confidence: 100            │
  └──────┬───────────────────────┘
         │ miss
         ▼
  ┌──────────────────────────────┐
  │  Tier 2: FUZZY CATALOG      │   ← Strip packaging noise, trigram similarity
  │  strip_packaging(text) →    │      against Product.name
  │  similarity > 0.65 → match  │      Confidence: 65-95 based on score
  └──────┬───────────────────────┘
         │ miss
         ▼
  ┌──────────────────────────────┐
  │  Tier 3: LLM HEURISTIC      │   ← Ask Gemini "which of these products
  │  top 3 suggestions with     │      best matches this supplier line?"
  │  reasoning                  │      Confidence: 30-70
  └──────┬───────────────────────┘
         │ miss
         ▼
  ┌──────────────────────────────┐
  │  UNMATCHED                   │   ← Requires manual clerk selection
  │  Confidence: 0               │      or "Create New Product" flow
  └──────────────────────────────┘
```

**Tier 1: Exact Supplier Alias Lookup**

```python
# server/modules/remitos/matching.py — Tier 1, 2 & 3 product resolution (< 120 LOC)


async def tier1_exact_alias(
    db: AsyncSession,
    supplier_name: str,
    raw_description: str,
) -> SupplierProductMapping | None:
    """O(1) cached lookup by normalized (supplier, text) pair."""
    normalized = normalize_supplier_text(raw_description)
    supplier_norm = supplier_name.lower().strip()

    stmt = select(SupplierProductMapping).where(
        SupplierProductMapping.supplier_name == supplier_norm,
        SupplierProductMapping.raw_item_pattern == normalized,
    )
    result = await db.scalars(stmt)
    mapping = result.first()

    if mapping:
        # Bump usage stats
        mapping.times_used += 1
        mapping.last_matched_at = datetime.now(timezone.utc)

    return mapping
```

**Tier 2: Fuzzy Catalog Matching**

```python
# Packaging noise words to strip before fuzzy matching
PACKAGING_NOISE = re.compile(
    r"\b(?:x\s*\d+\s*(?:u|un|unidades?|gr?|kg|kilos?|lt?|ml|cc))"
    r"|\b(?:caja|pack|bolsa|display|promo|oferta|sachet|sobre)\b"
    r"|\b(?:de|el|la|los|las|por|con|sin)\b"
    r"|[()[\]{}\-–—/\\|.,;:!?\"'`x×]",
    re.IGNORECASE,
)


def strip_packaging_noise(text: str) -> str:
    """Remove packaging descriptors and noise words for product name comparison."""
    cleaned = PACKAGING_NOISE.sub(" ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower()


async def tier2_fuzzy_match(
    db: AsyncSession,
    raw_description: str,
    limit: int = 5,
) -> list[tuple[Product, int]]:
    """Fuzzy match against Product.name using trigram similarity.

    Returns list of (Product, confidence_score) tuples sorted by score descending.
    Requires PostgreSQL pg_trgm extension.
    """
    cleaned = strip_packaging_noise(raw_description)

    if not cleaned or len(cleaned) < 3:
        return []

    # PostgreSQL trigram similarity query
    stmt = text("""
        SELECT id, name, sku, similarity(LOWER(name), :query) AS score
        FROM products
        WHERE similarity(LOWER(name), :query) > 0.3
        ORDER BY score DESC
        LIMIT :limit
    """)

    result = await db.execute(stmt, {"query": cleaned, "limit": limit})
    rows = result.fetchall()

    matches = []
    for row in rows:
        product = await db.get(Product, row.id)
        if product:
            # Scale similarity (0.0-1.0) to confidence (0-100)
            confidence = min(95, int(row.score * 100))
            matches.append((product, confidence))

    return matches
```

> **Note**: Requires `CREATE EXTENSION IF NOT EXISTS pg_trgm;` in PostgreSQL. For SQLite test harness, Tier 2 falls through to Tier 3 or returns empty.

**Tier 3: LLM Heuristic Fallback**

When neither alias cache nor fuzzy matching produces a confident result, we query the same vision model with a product catalog subset:

```python
async def tier3_llm_match(
    raw_description: str,
    candidate_products: list[Product],
) -> list[tuple[int, int, str]]:
    """Ask LLM which product best matches a supplier line item.

    Returns: list of (product_id, confidence, reasoning) tuples, max 3.
    """
    catalog_text = "\n".join(
        f"- ID={p.id} | SKU={p.sku} | Name={p.name} | Type={p.product_type}"
        for p in candidate_products[:30]  # Cap to avoid token bloat
    )

    response = await _client.chat.completions.create(
        model=PRIMARY_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a product matching assistant for an Argentine "
                    "dietética store. Given a supplier line item description "
                    "and a list of internal catalog products, return the top 3 "
                    "most likely matches as JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f'Supplier line: "{raw_description}"\n\n'
                    f"Internal catalog:\n{catalog_text}\n\n"
                    'Return JSON: [{"product_id": int, "confidence": 0-100, '
                    '"reasoning": "..."}] (max 3 entries, sorted by confidence desc)'
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=512,
    )

    # Parse and return
    data = json.loads(response.choices[0].message.content)
    matches = data.get("matches", data) if isinstance(data, dict) else data
    return [
        (m["product_id"], m["confidence"], m.get("reasoning", "")) for m in matches[:3]
    ]
```

### 4.2 Packaging Multiplier Detection

The packaging parser extracts the conversion multiplier from the raw supplier description text using a hierarchy of regex patterns tuned for Argentine wholesale formatting conventions.

```python
# server/modules/remitos/converter.py — packaging parser (< 90 LOC)

import re
from dataclasses import dataclass

from server.modules.catalog.models import ProductType


@dataclass
class PackageParseResult:
    """Result of parsing a supplier description for packaging information."""

    package_type: str  # "caja", "pack", "bolsa", "display", "unidad", "kg"
    multiplier: int  # Units per package (or grams for bulk)
    target_unit_type: str  # "discrete_unit" or "bulk_grams"
    inner_weight_grams: int | None  # Weight per inner unit if detected (e.g. 41g)
    confidence: int  # 0-100


# Ordered by specificity — first match wins
MULTIPLIER_PATTERNS = [
    # "x 10 u" / "x 10 unidades" / "x10u" / "× 10 un"
    (r"[x×]\s*(\d+)\s*(?:u(?:n(?:idades?)?)?\.?)\b", "caja"),
    # "pack de 6" / "pack x 6" / "pack 6u"
    (r"pack\s*(?:de|x)?\s*(\d+)", "pack"),
    # "display x 12" / "display de 24"
    (r"display\s*(?:de|x)?\s*(\d+)", "display"),
    # "caja x 20" / "caja de 12"
    (r"caja\s*(?:de|x)?\s*(\d+)", "caja"),
    # "bolsa x 5 kg" (bulk — multiplier = 5000 grams)
    (r"(?:bolsa|bolson)\s*(?:de|x)?\s*(\d+(?:[.,]\d+)?)\s*(?:kg|kilos?)", "bolsa_kg"),
    # "x 2 kg" / "2 kg" (standalone weight for bulk)
    (r"[x×]\s*(\d+(?:[.,]\d+)?)\s*(?:kg|kilos?)", "kg"),
    # "x 500 gr" / "500 g" (sub-kilo weight)
    (r"[x×]\s*(\d+)\s*(?:gr?(?:amos?)?)", "grams"),
]

# Inner unit weight detection (e.g. "x 41 gr" within "Barritas x 41 gr x 10 u")
INNER_WEIGHT_PATTERN = re.compile(r"(\d+)\s*(?:gr?(?:amos?)?)\b", re.IGNORECASE)


def parse_packaging(
    raw_description: str,
    product_type: ProductType | None = None,
) -> PackageParseResult:
    """Extract packaging multiplier and type from supplier item description.

    Examples:
        "Barritas Almendra x 41 gr x 10 u (Integra)"
            → PackageParseResult(package_type="caja", multiplier=10,
              target_unit_type="discrete_unit", inner_weight_grams=41)

        "Yerba Kalena x 2 kg x 5 u"
            → PackageParseResult(package_type="caja", multiplier=5,
              target_unit_type="discrete_unit", inner_weight_grams=None)

        "Almendras Peladas x 10 kg"
            → PackageParseResult(package_type="kg", multiplier=10000,
              target_unit_type="bulk_grams", inner_weight_grams=None)
    """
    text = raw_description.lower().strip()

    # Try each pattern
    for pattern, pkg_type in MULTIPLIER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_value = match.group(1).replace(",", ".")
            value = float(raw_value)

            if pkg_type == "bolsa_kg":
                # Bulk bag: convert kg to grams
                return PackageParseResult(
                    package_type="bolsa",
                    multiplier=int(value * 1000),
                    target_unit_type="bulk_grams",
                    inner_weight_grams=None,
                    confidence=85,
                )
            elif pkg_type == "kg":
                # Check if this is a bulk product or a discrete pack
                if product_type == ProductType.BULK:
                    return PackageParseResult(
                        package_type="kg",
                        multiplier=int(value * 1000),
                        target_unit_type="bulk_grams",
                        inner_weight_grams=None,
                        confidence=80,
                    )
                else:
                    # Discrete product sold in kg packages (e.g. "Yerba x 2 kg")
                    # Multiplier = 1 (one package = one sellable unit)
                    return PackageParseResult(
                        package_type="kg",
                        multiplier=1,
                        target_unit_type="discrete_unit",
                        inner_weight_grams=int(value * 1000),
                        confidence=75,
                    )
            elif pkg_type == "grams":
                if product_type == ProductType.BULK:
                    return PackageParseResult(
                        package_type="grams",
                        multiplier=int(value),
                        target_unit_type="bulk_grams",
                        inner_weight_grams=None,
                        confidence=80,
                    )
                else:
                    # Weight descriptor for a discrete item (e.g. "galletas x 150 g")
                    return PackageParseResult(
                        package_type="unidad",
                        multiplier=1,
                        target_unit_type="discrete_unit",
                        inner_weight_grams=int(value),
                        confidence=70,
                    )
            else:
                # Standard unit multiplier (caja, pack, display)
                inner_wt = None
                wt_match = INNER_WEIGHT_PATTERN.search(text)
                if wt_match:
                    inner_wt = int(wt_match.group(1))

                return PackageParseResult(
                    package_type=pkg_type,
                    multiplier=int(value),
                    target_unit_type="discrete_unit",
                    inner_weight_grams=inner_wt,
                    confidence=90,
                )

    # No packaging pattern detected — assume single unit
    return PackageParseResult(
        package_type="unidad",
        multiplier=1,
        target_unit_type="discrete_unit",
        inner_weight_grams=None,
        confidence=50,
    )
```

### 4.3 Fiscal Split & True Net Unit Cost Computation

Argentine wholesale distributors commonly split deliveries between *blanco* (formally invoiced with IVA) and *negro* (informally invoiced without tax documentation). The real cost to the retailer must account for this split to compute accurate margin data.

#### Mathematical Formulation

Given:
- **P<sub>pack</sub>** = Wholesale package list price (as printed on remito, whole ARS)
- **f<sub>blanco</sub>** = Fraction of order billed formally con factura (e.g. 0.60)
- **f<sub>negro</sub>** = Fraction of order billed informally sin factura (e.g. 0.40), where f<sub>blanco</sub> + f<sub>negro</sub> = 1.0
- **r<sub>iva</sub>** = IVA rate applied to the blanco portion (e.g. 0.21 for 21%)
- **M** = Conversion multiplier (sellable units per package, or total grams for bulk)
- **d** = Global discount percentage (0-100, default 0)

**Step 1: Effective Cost Factor**

The printed price on the remito is the *base* price. The blanco portion has IVA added on top:

```
Effective Cost Factor = f_negro + f_blanco × (1 + r_iva)
```

For a typical 60% blanco / 40% negro split with 21% IVA:
```
Factor = 0.40 + 0.60 × 1.21 = 0.40 + 0.726 = 1.126
```

**Step 2: Real Landed Package Cost**

```
Real Pack Cost = P_pack × Factor × (1 - d/100)
```

**Step 3: Real Net Unit Cost (Discrete Products)**

```
Unit Cost = round(Real Pack Cost / M)     # Integer ARS, banker's rounding
```

**Step 4: Real Net Cost per Reference Weight (Bulk Products)**

For bulk products (sold by 100g reference weight):
```
Cost per 100g = round(Real Pack Cost / Total Grams × 100)    # Integer ARS
```

#### Implementation

```python
# server/modules/remitos/fiscal.py — unit cost & fiscal split arithmetic (< 80 LOC)

from dataclasses import dataclass


@dataclass
class FiscalCostResult:
    """Result of fiscal split cost computation."""

    effective_factor_bps: int  # Cost factor in basis points (e.g. 11260 = 1.126)
    real_pack_cost: int  # Landed package cost (whole ARS)
    real_unit_cost: int  # Cost per sellable unit (whole ARS)
    iva_amount_per_pack: int  # IVA portion per package (whole ARS)


def compute_unit_cost(
    pack_price: int,
    multiplier: int,
    blanco_bps: int = 6000,
    negro_bps: int = 4000,
    iva_rate_bps: int = 2100,
    discount_pct: int = 0,
    is_bulk: bool = False,
    bulk_reference_grams: int = 100,
) -> FiscalCostResult:
    """Compute real net unit cost accounting for Argentine fiscal split.

    All monetary values are in whole Argentine Pesos (integer ARS).
    Ratios are in basis points (6000 = 60%, 2100 = 21%).

    Args:
        pack_price: Wholesale package list price (whole ARS).
        multiplier: Sellable units per package (or total grams for bulk).
        blanco_bps: Formal invoice fraction in basis points.
        negro_bps: Informal fraction in basis points.
        iva_rate_bps: IVA rate in basis points (applied to blanco only).
        discount_pct: Global discount percentage (0-100).
        is_bulk: True for bulk products (cost per reference weight).
        bulk_reference_grams: Reference weight for bulk pricing (default 100g).

    Returns:
        FiscalCostResult with all computed values.

    Example:
        1 Caja of 10 bars @ $5,000/caja, 60% blanco, 40% negro, 21% IVA:
        Factor = 0.40 + 0.60 × 1.21 = 1.126
        Real pack cost = 5000 × 1.126 = 5630
        Unit cost = round(5630 / 10) = 563 ARS per bar
    """
    if multiplier <= 0:
        raise ValueError(f"Multiplier must be positive, got {multiplier}")

    # Convert basis points to fractions (using integer arithmetic)
    # factor_bps = negro_bps + blanco_bps × (10000 + iva_rate_bps) / 10000
    # To avoid float: compute in scaled integers
    factor_bps = negro_bps + (blanco_bps * (10000 + iva_rate_bps)) // 10000

    # Real pack cost (with discount)
    # real_pack_cost = pack_price × factor_bps / 10000 × (100 - discount_pct) / 100
    real_pack_cost_scaled = pack_price * factor_bps * (100 - discount_pct)
    real_pack_cost = (real_pack_cost_scaled + 500_000) // 1_000_000  # Round

    # IVA amount per pack
    iva_per_pack = (pack_price * blanco_bps * iva_rate_bps + 50_000_000) // 100_000_000

    # Unit cost
    if is_bulk and multiplier > 0:
        # Cost per bulk_reference_grams (e.g. per 100g)
        # unit_cost = real_pack_cost × reference_grams / total_grams
        real_unit_cost = (
            real_pack_cost * bulk_reference_grams + multiplier // 2
        ) // multiplier
    else:
        # Cost per discrete unit
        real_unit_cost = (real_pack_cost + multiplier // 2) // multiplier

    return FiscalCostResult(
        effective_factor_bps=factor_bps,
        real_pack_cost=real_pack_cost,
        real_unit_cost=real_unit_cost,
        iva_amount_per_pack=iva_per_pack,
    )
```

**Worked Examples**:

| Scenario | Pack Price | Split | IVA | Multiplier | Factor | Real Pack | Unit Cost |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 Caja Barritas × 10 u | $5,000 | 60/40 | 21% | 10 | 1.126 | $5,630 | **$563/bar** |
| 1 Pack Yerba × 5 u | $12,000 | 60/40 | 21% | 5 | 1.126 | $13,512 | **$2,702/pack** |
| 1 Bolsa Almendras × 10 kg | $45,000 | 60/40 | 21% | 10,000g | 1.126 | $50,670 | **$507/100g** |
| 1 Caja Té × 20 u (all negro) | $8,000 | 0/100 | 21% | 20 | 1.000 | $8,000 | **$400/caja** |
| 1 Caja Mix × 12 u (all blanco) | $6,000 | 100/0 | 21% | 12 | 1.210 | $7,260 | **$605/unit** |

---

## 5. API Contract & Endpoints

All endpoints are defined in the thin HTTP coordinator `server/modules/remitos/router.py` (< 130 LOC), backed by domain service orchestration in `server/modules/remitos/service.py` (< 140 LOC), and explicitly mounted in the aggregate router `server/api/v1/router.py`:

```python
# server/api/v1/router.py
from fastapi import APIRouter
from server.modules.catalog.router import router as catalog_router
from server.modules.identity.router import router as identity_router
from server.modules.inventory.router import router as inventory_router
from server.modules.remitos.router import router as remitos_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(identity_router)
v1_router.include_router(catalog_router)
v1_router.include_router(inventory_router)
v1_router.include_router(remitos_router)
```

### 5.1 Endpoint Summary

| Method | Path | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/remitos/scan-and-stage` | Upload receipt images, run vision pipeline, return staged remito | 201, 400, 422, 502 |
| `GET` | `/remitos` | List remitos with status/date filters | 200 |
| `GET` | `/remitos/{id}` | Get full remito detail with items | 200, 404 |
| `PUT` | `/remitos/{id}/items/{item_id}` | Inline edit a staged remito item | 200, 404, 409 |
| `POST` | `/remitos/{id}/confirm` | Commit stock, create ledger entries | 200, 404, 409 |
| `POST` | `/remitos/{id}/reject` | Reject/discard a staged remito | 200, 404, 409 |
| `GET` | `/supplier-mappings` | List supplier alias cache entries | 200 |
| `DELETE` | `/supplier-mappings/{id}` | Delete a cached mapping | 200, 404 |

### 5.2 `POST /remitos/scan-and-stage`

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `images` | `UploadFile[]` | Yes | 1-4 receipt page photos (JPEG/PNG/WebP) |
| `supplier_name` | `str` | No | Override auto-detected supplier name |
| `fiscal_blanco_pct` | `int` | No | Override blanco % (default: 60) |
| `fiscal_negro_pct` | `int` | No | Override negro % (default: 40) |
| `iva_pct` | `int` | No | Override IVA % (default: 21) |

**Response**: `201 Created`

```json
{
  "id": 42,
  "remito_number": "0001-00045231",
  "supplier_name": "New Day Distribuidora",
  "date_issued": "2026-10-08",
  "status": "staged",
  "page_count": 2,
  "fiscal_blanco_bps": 6000,
  "fiscal_negro_bps": 4000,
  "iva_rate_bps": 2100,
  "total_raw_amount": 285000,
  "total_real_amount": 320910,
  "overall_confidence": 92,
  "extraction_notes": ["Página 1 y 2 procesadas correctamente (solo texto impreso)."],
  "items": [
    {
      "id": 101,
      "line_index": 0,
      "raw_description": "Barritas Almendra x 41 gr x 10 u (Integra)",
      "extracted_quantity": 1,
      "extracted_unit_cost": 5000,
      "extracted_line_total": 5000,
      "product_id": 15,
      "product_name": "Barrita Almendra Integra 41g",
      "product_sku": "BAR-ALM-INTEGRA-41G",
      "package_type": "caja",
      "multiplier": 10,
      "target_unit_type": "discrete_unit",
      "effective_quantity": 1,
      "quantity_to_commit": 10,
      "calculated_unit_cost": 563,
      "match_confidence": 100,
      "match_strategy": "exact_alias",
      "is_verified_by_user": false
    },
    {
      "id": 102,
      "line_index": 1,
      "raw_description": "Yerba Kalena x 2 kg x 5 u",
      "extracted_quantity": 2,
      "extracted_unit_cost": 12000,
      "extracted_line_total": 24000,
      "product_id": 8,
      "product_name": "Yerba Kalena 2kg",
      "product_sku": "YERBA-KALENA-2KG",
      "package_type": "pack",
      "multiplier": 5,
      "target_unit_type": "discrete_unit",
      "effective_quantity": 2,
      "quantity_to_commit": 10,
      "calculated_unit_cost": 2702,
      "match_confidence": 78,
      "match_strategy": "fuzzy_catalog",
      "is_verified_by_user": false
    }
  ]
}
```

**Error Responses**:
- `400 Bad Request`: No images uploaded, or invalid image format.
- `422 Unprocessable Entity`: Vision pipeline returned unparseable output.
- `502 Bad Gateway`: OpenRouter API unreachable or rate-limited.

### 5.3 `POST /remitos/{id}/confirm`

**Request**: Empty body (or optional override JSON).

**Precondition**: `remito.status == "staged"`.

**Transaction Steps** (atomic):

1. Validate all items with `quantity_to_commit > 0` have a `product_id`.
2. For each matched item:
   a. `SELECT FOR UPDATE` on `products` row (via existing `_get_locked_product`).
   b. `product.current_stock += item.quantity_to_commit`.
   c. `product.last_cost = item.calculated_unit_cost`.
   d. Insert `InventoryLedger` entry:
      - `movement_type = "receiving"`
      - `quantity_delta = item.quantity_to_commit`
      - `balance_after = product.current_stock`
      - `reference_id = f"REMITO-{remito.id}"`
      - `notes = f"Remito {remito.remito_number} - {item.raw_description}"`
3. For each verified item, `UPSERT` into `supplier_product_mappings`:
   - Key: `(supplier_name, normalized_pattern)`
   - Values: `product_id`, `multiplier`, `package_type`, `target_unit_type`
4. Set `remito.status = "committed"`, `remito.committed_at = now()`.
5. `COMMIT` transaction.

**Response**: `200 OK` with summary of committed items and ledger entry IDs.

**Error Responses**:
- `404 Not Found`: Remito ID does not exist.
- `409 Conflict`: Remito is not in `staged` status (already committed/rejected), or items have `product_id = null`.

### 5.4 `PUT /remitos/{id}/items/{item_id}`

**Request Body**:

```json
{
  "product_id": 15,
  "multiplier": 10,
  "package_type": "caja",
  "target_unit_type": "discrete_unit",
  "effective_quantity": 1,
  "is_verified_by_user": true
}
```

All fields are optional — only provided fields are updated. On any change:
- Recompute `quantity_to_commit = effective_quantity × multiplier`.
- Recompute `calculated_unit_cost` using fiscal split parameters from the parent `remito`.
- Set `match_strategy = "manual_override"` if `product_id` was changed.
- Set `match_confidence = 100` and `is_verified_by_user = true` on manual selection.

### 5.5 `POST /remitos/{id}/reject`

Sets `remito.status = "rejected"`. No inventory changes. Irreversible.

### 5.6 Configuration Extension

```python
# server/core/config.py — additions


class Settings(BaseSettings):
    # ... existing fields ...

    # OpenRouter Vision Pipeline
    openrouter_api_key: str = ""
    openrouter_primary_model: str = "google/gemini-2.0-flash-001"
    openrouter_fallback_model: str = "anthropic/claude-3.5-sonnet"
    remito_default_blanco_pct: int = 60
    remito_default_negro_pct: int = 40
    remito_default_iva_pct: int = 21
```

---

## 6. Staging UI Requirements

### 6.1 Route & Component Architecture

| Route | File | Description |
| :--- | :--- | :--- |
| `/remitos` | `apps/admin/src/routes/remitos/+page.svelte` | Remito list with status tabs |
| `/remitos/new` | `apps/admin/src/routes/remitos/new/+page.svelte` | Upload photos & trigger scan |
| `/remitos/[id]` | `apps/admin/src/routes/remitos/[id]/+page.svelte` | Staging review & commit screen |

### 6.2 Staging Review Screen Layout (`/remitos/[id]`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Volver    Remito #0001-00045231    New Day Distribuidora    2026-10-08│
│              Status: 🟡 STAGED (Pendiente de Revisión)                 │
├─────────────────────┬───────────────────────────────────────────────────┤
│                     │                                                   │
│   📸 Receipt Photo  │   📋 Extracted Items                              │
│   ┌───────────────┐ │   ┌──────────────────────────────────────────┐   │
│   │               │ │   │ # │ Desc           │ Qty│ ×  │ Commit   │   │
│   │  Pan/Zoom     │ │   │───│────────────────│────│────│──────────│   │
│   │  Lightbox     │ │   │🟢1│ Barritas Alm…  │  1 │ 10 │ +10 u   │   │
│   │               │ │   │🟡2│ Yerba Kalena…  │ 1̶→1│  5 │ +5 u    │   │
│   │  (swipe for   │ │   │🔴3│ Granola Mix…   │  3 │  ? │ ???     │   │
│   │   page 2)     │ │   │🟣4│ Chía x 5 kg   │  2̶  │ -- │ 0 (✗)  │   │
│   │               │ │   └──────────────────────────────────────────┘   │
│   └───────────────┘ │                                                   │
│                     │   ┌── Fiscal Split ──────────────────────────┐   │
│   Page 1/2  ●○      │   │ Blanco: [====60%====] Negro: [==40%==]  │   │
│                     │   │ IVA:    [==21%==]      Desc: [0%]       │   │
│                     │   │ Total Factura: $285,000  Real: $320,910 │   │
│                     │   └─────────────────────────────────────────┘   │
│                     │                                                   │
│                     │   [ Rechazar Remito ]     [ ✓ Confirmar Stock ] │
└─────────────────────┴───────────────────────────────────────────────────┘
```

### 6.3 Audit Status Indicators (Color-Coded Badges)

| Badge | Color | Meaning | User Action Required |
| :--- | :--- | :--- | :--- |
| 🟢 | Green (`bg-emerald-100 text-emerald-800`) | **Auto-Matched** — Exact alias cache hit or high-confidence fuzzy match (≥80%). | None (click to inspect). |
| 🟡 | Amber (`bg-amber-100 text-amber-800`) | **Review Required** — Fuzzy match with confidence 50–79%, or low OCR confidence. | Verify product match and multiplier. |
| 🔴 | Red (`bg-red-100 text-red-800`) | **Unmatched** — No product resolution found in catalog. | Select product manually or create new. |

### 6.4 Inline Editing & Override Controls

Each row in the staging table supports:

1. **Product Picker** — Searchable dropdown (combobox) to override `product_id`. Triggers `PUT /remitos/{id}/items/{item_id}` with `match_strategy = "manual_override"`.
2. **Multiplier Editor** — Numeric input to adjust the packaging conversion. Recalculates `quantity_to_commit` and `calculated_unit_cost` in real-time.
3. **Quantity Override / Exclusion** — Edit `effective_quantity` (e.g. if an item physically arrived short, or set to `0` / click trash icon if an item was crossed out on paper).
4. **"Crear Producto Rápido"** — For 🔴 unmatched items: inline modal to create a new `Product` with minimal fields (SKU, name, price, type), then auto-link.

### 6.5 Fiscal Split Controls

- **Sliders or paired inputs** for `% Blanco` and `% Negro` (must sum to 100).
- **IVA % input** (default 21, supports 10.5 for certain food categories).
- **Global discount %** input.
- Changes trigger immediate recalculation of all `calculated_unit_cost` values across all items via `PATCH` to the remito header.

### 6.6 Confirmation Gate

The **"✓ Confirmar Stock"** button is **disabled** until:
1. Zero 🔴 (unmatched) items remain (all must be resolved or explicitly excluded).
2. The mathematical audit check passes (sum of line totals ≈ header total ± 1%).

### 6.7 Technology Stack

- **Svelte 5 Runes**: `$state` for form inputs, `$derived` for computed totals.
- **`@tanstack/svelte-query`**: Mutations for item updates and confirmation.
- **`@vitalcer/ui`**: `Button`, `Card`, `Dialog`, `Input`, `Badge` from shared component library.
- **`@vitalcer/api`**: Auto-generated client from OpenAPI spec via `make codegen`.
- **Image Viewer**: Pinch-zoom lightbox (e.g. `medium-zoom` or native CSS `object-fit: contain` with `overflow: scroll`).

---

## 7. Edge Cases, Failure Modes & Error Handling

### 7.1 Mathematical Audit Validation

After extraction, the system performs an automatic cross-check:

```python
def validate_line_totals(
    items: list[ExtractedLineItem], fiscal_total: int | None
) -> tuple[bool, int]:
    """Check if sum of extracted line totals matches document total.

    Returns: (is_valid, discrepancy_ars)
    """
    computed_sum = sum(item.extracted_line_total for item in items)

    if fiscal_total is None or fiscal_total == 0:
        return True, 0  # No total to validate against

    discrepancy = abs(computed_sum - fiscal_total)
    # Allow 1% tolerance for rounding
    threshold = max(fiscal_total // 100, 1)
    return discrepancy <= threshold, discrepancy
```

**UI Behavior**: If discrepancy > 1%, display a warning banner: *"⚠️ La suma de líneas ($X) difiere del total del documento ($Y) en $Z. Revise las cantidades y precios."*

### 7.2 Multi-Page Receipt Handling

1. **Page Detection**: Vision prompt instructs model to detect "Pag X/Y", "Hoja X de Y", or page numbering.
2. **Item Stitching**: Items from all pages are merged into a single `items` array, with `line_index` continuing sequentially.
3. **Header De-duplication**: If supplier name/number appears on every page, only the first occurrence is used.
4. **Footer Totals**: Only the last page's total is considered (earlier pages may show subtotals).

### 7.3 Printed-Only Extraction & Human Physical Reconciliation

By design, the AI vision pipeline **extracts only printed text and ignores handwriting**:

* **Why ignore handwriting?** Ballpoint pen strokes on carbon paper (Recibos X) vary wildly, causing high OCR hallucination rates (e.g. misreading a scratch as an 8, or treating pen checks as crossed-out text). Eliminating handwriting detection makes the vision layer fast, cheap, deterministic, and highly accurate.
* **How physical adjustments are handled**: The physical delivery receipt photo is displayed directly in the left pane of the review screen (`/remitos/[id]`). If the driver or clerk made handwritten notes (e.g. cross-outs for missing items or scribbled quantity adjustments), the clerk adjusts the `effective_quantity` field in the table with one click or clicks the trash icon to zero out that line item.

### 7.4 Unrecognized Products

When catalog matching fails across all three tiers:

1. Item is flagged as `match_strategy = "unmatched"` with `match_confidence = 0`.
2. UI displays a 🔴 badge and blocks confirmation until resolved.
3. Clerk has two options:
   a. **Search & Link**: Use the product picker combobox to find the existing product.
   b. **Create New**: Open "Crear Producto Rápido" inline modal. Minimal required fields:
      - `sku` (auto-suggested from supplier text)
      - `name` (pre-filled from extracted description)
      - `unit_price` (pre-filled from calculated cost × 1.5 as suggested retail)
      - `product_type` (discrete/bulk)
      The newly created product is immediately linked to the remito item and a supplier alias mapping is created on confirm.

### 7.5 Image Quality Issues

| Issue | Detection Method | User Feedback |
| :--- | :--- | :--- |
| **Blurred / out of focus** | Vision model returns `overall_confidence < 40` | *"Imagen borrosa. Por favor tome la foto nuevamente con mejor iluminación."* |
| **Excessive glare / reflection** | Low confidence on specific lines | Affected lines flagged with `requires_human_review = true` |
| **Rotated / skewed** | EXIF auto-rotation + Vision model's built-in orientation handling | Transparent — handled automatically |
| **Partial / cropped** | Vision detects cut-off lines at edges | *"Posible contenido cortado en los bordes. Verifique que toda la hoja sea visible."* |
| **Corrupt file** | PIL/Pillow fails to open | `400 Bad Request`: *"Archivo de imagen corrupto o formato no soportado."* |

### 7.6 Double-Commit Prevention

```python
async def confirm_remito(db: AsyncSession, remito_id: int) -> Remito:
    # Lock the remito row
    stmt = select(Remito).where(Remito.id == remito_id).with_for_update()
    remito = (await db.scalars(stmt)).first()

    if not remito:
        raise EntityNotFoundError("Remito", remito_id)

    if remito.status != RemitoStatus.STAGED:
        raise InvalidMovementError(
            f"Remito {remito_id} is '{remito.status}', expected 'staged'. "
            f"Cannot confirm a remito that is already {remito.status}."
        )

    # ... proceed with stock commit ...
```

The `SELECT FOR UPDATE` on the `remitos` row prevents two concurrent confirm requests from executing simultaneously.

### 7.7 OpenRouter API Failures

| Failure | Handling |
| :--- | :--- |
| **Rate limited (429)** | Exponential backoff with 3 retries, max wait 30s |
| **Server error (500/502/503)** | Retry once after 2s, then fail with `502 Bad Gateway` |
| **Timeout (>30s)** | Fail immediately, suggest retrying with fewer pages |
| **Invalid JSON response** | Retry once with explicit JSON instruction appended, then fail with `422` |
| **API key invalid (401)** | Fail immediately with configuration error log |

---

## 8. Implementation Roadmap

### Phase 1: Core Modular Extraction, Packaging Converter & Fiscal Engine (< 140 LOC / Module)

**Goal**: Extract proven algorithms from `scripts/spike_remito_vision.py` into production-ready vertical modules under `server/modules/remitos/` conforming to the 250 LOC blueprint.

| Task | Deliverable | Target LOC | Focus & Standards |
| :--- | :--- | :--- | :--- |
| Pydantic Schemas | `server/modules/remitos/schemas.py` | < 100 LOC | `ExtractedLineItem`, `ExtractedFiscalInfo`, `RemitoVisionOutput`, API DTOs |
| Vision Client & Preprocessor | `server/modules/remitos/client.py` | < 120 LOC | OpenRouter client, EXIF auto-rotation, WebP compression, system prompt |
| Packaging Converter | `server/modules/remitos/converter.py` | < 90 LOC | Regex packaging multiplier detection (`x 10 u`, `pack de 6`, `kg`) |
| Fiscal Calculator | `server/modules/remitos/fiscal.py` | < 80 LOC | 60/40 fiscal split, basis points calculations (6000/4000/2100 bps), integer ARS |
| Converter Unit Tests | `tests/remitos/test_converter.py` | < 100 LOC | Unit test suite for packaging pattern detection & bulk conversions |
| Fiscal Math Unit Tests | `tests/remitos/test_fiscal.py` | < 100 LOC | Unit test suite for 60/40 split, IVA, and integer rounding |
| Offline Test Fixtures | `tests/fixtures/remitos/*.json` | Fixtures | Mock LLM responses for New Day remitos (guarantees zero live paid calls) |

### Phase 2: Database Schema, 3-Tier Matcher, Atomic Commit Engine & API Router

**Goal**: Full backend API with SQLModel persistence, cross-slice decoupling, double-entry ledger commit, and thin HTTP routing.

| Task | Deliverable | Target LOC | Focus & Standards |
| :--- | :--- | :--- | :--- |
| SQLModel Models | `server/modules/remitos/models.py` | < 140 LOC | `Remito`, `RemitoItem`, `SupplierProductMapping` tables |
| Product Extension | `server/modules/catalog/models.py` | Addition | Add `last_cost: int \| None` column |
| Models Registry | `server/core/models_registry.py` | Addition | Register `server.modules.remitos.models` in deterministic order |
| Catalog Matcher | `server/modules/remitos/matching.py` | < 120 LOC | 3-tier product resolution (Tier 1 alias → Tier 2 trigram → Tier 3 LLM) |
| Remito Service Engine | `server/modules/remitos/service.py` | < 140 LOC | Scan-and-stage, double-entry commit (`_get_locked_product`), alias upsert |
| Thin API Router | `server/modules/remitos/router.py` | < 130 LOC | HTTP coordinator delegating to `service.py`, global exception handlers |
| Router Registration | `server/api/v1/router.py` | Addition | `v1_router.include_router(remitos_router)` |
| Matcher Unit Tests | `tests/remitos/test_matching.py` | < 110 LOC | Test alias cache hit, trigram fuzzy matching, normalization |
| Service & Commit Tests | `tests/remitos/test_service.py` | < 120 LOC | Test double-entry receiving commit, `last_cost` update, locking |
| Endpoint Integration Tests | `tests/remitos/test_router.py` | < 120 LOC | Test all 8 endpoints with test client and mock vision fixtures |
| OpenAPI Codegen | `make codegen` | Automated | Export OpenAPI spec and regenerate `@vitalcer/api` client types |

### Phase 3: Backoffice Staging UI & Inbound Stock Workflow

**Goal**: Clerk-facing UI for review, side-by-side receipt audit, manual override, and atomic stock commitment.

| Task | Deliverable | Focus & Standards |
| :--- | :--- | :--- |
| Remito List View | `apps/admin/src/routes/remitos/+page.svelte` | Staged/Committed tabs, supplier and date filters, KPI summary cards |
| Multi-Photo Upload | `apps/admin/src/routes/remitos/new/+page.svelte` | Multi-page file dropzone, camera upload, scan progress bar |
| Staging Review Screen | `apps/admin/src/routes/remitos/[id]/+page.svelte` | Side-by-side receipt photo pan/zoom lightbox ↔ editable data grid |
| Product Combobox | `@vitalcer/ui` Combobox / Picker | Searchable catalog dropdown with keyboard navigation for manual overrides |
| Fiscal Split Sliders | Component in `/remitos/[id]` | Real-time sliders for blanco/negro/IVA triggering dynamic recalculation |
| Quick Product Modal | Inline modal in `/remitos/[id]` | Fast creation of new `Product` for 🔴 unmatched items |
| Atomic Commit Action | Confirm Button in `/remitos/[id]` | Wired to `POST /confirm` with optimistic toast feedback |
| Navigation Integration | Admin layout navigation | Add "Remitos" link with staging badge counter |

### Phase 4: Productionization, Monorepo Verification & Spike Governance Gate

**Goal**: Verify architectural compliance with [`AGENTS.md`](../AGENTS.md) and [`docs/backend_refactoring_plan.md`](backend_refactoring_plan.md).

| Gate / Requirement | Verification Protocol | Success Criteria |
| :--- | :--- | :--- |
| **Spike Governance** | Check `scripts/spike_remito_vision.py` | Verified standalone spike header; zero imports in `server/` |
| **Zero Paid API Calls** | Audit CI & test runners | Automated tests use offline mock fixtures only; zero live calls |
| **250 LOC Ceiling** | Line count audit (`wc -l server/modules/remitos/*.py`) | Every file < 140 LOC (well below 250 LOC hard limit) |
| **Modular Test Ceiling** | Line count audit (`wc -l tests/remitos/*.py`) | Every test file < 120 LOC |
| **Lint & Style** | `make lint` | Zero errors across `ruff` and `biome` |
| **Strict Typecheck** | `make typecheck` | Zero errors across all domain modules |
| **Test Suite** | `make test` | 100% passing tests on SQLite in-memory harness |
| **OpenAPI Contract** | `make openapi` | Canonical key-sorted OpenAPI spec diff is clean |
| **Full Validation** | `make check` | Monorepo build passes without errors |

---

## Appendix A: Glossary

| Term | Definition |
| :--- | :--- |
| **Remito** | Argentine delivery note accompanying a physical goods shipment. Lists items, quantities, and sometimes prices. Not a tax invoice. |
| **Recibo X** | A generic receipt document type in Argentina, often used for informal or mixed-invoice deliveries. |
| **Blanco** | *"Con factura"* — the formally invoiced portion of a delivery, subject to IVA. |
| **Negro** | *"Sin factura"* — the informally invoiced portion, with no tax documentation. Common in Argentine wholesale distribution. |
| **IVA** | *Impuesto al Valor Agregado* — Argentine VAT, typically 21% for general goods, 10.5% for certain food items. |
| **Dietética** | An Argentine health food / dietary supplement store selling both packaged discrete goods and bulk items by weight. |
| **Merma** | Shrinkage — inventory loss due to spillage, spoilage, evaporation, tasting, or breakage. |
| **PLU** | Price Look-Up code — 4-digit code used by in-store electronic scales for bulk goods. |
| **Basis Points (bps)** | 1/100th of a percentage point. 100 bps = 1%, 2100 bps = 21%. Used for integer storage of percentages. |

## Appendix B: Environment Variables

```bash
# .env additions for Remito Ingestion
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
OPENROUTER_PRIMARY_MODEL=google/gemini-2.0-flash-001     # Optional override
OPENROUTER_FALLBACK_MODEL=anthropic/claude-3.5-sonnet     # Optional override
REMITO_DEFAULT_BLANCO_PCT=60
REMITO_DEFAULT_NEGRO_PCT=40
REMITO_DEFAULT_IVA_PCT=21
```
