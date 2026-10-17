#!/usr/bin/env python3
"""Vision Spike: Test OpenRouter vision extraction on Argentine delivery receipts.

Supports multiple models via OpenRouter (Gemini 2.0 Flash, Claude 3.5 Sonnet, etc.),
multi-page receipt image processing, and structured Pydantic extraction.

Usage:
    # Using default model (google/gemini-2.0-flash-001)
    python scripts/spike_remito_vision.py path/to/remito_page1.jpg

    # Multi-page receipt
    python scripts/spike_remito_vision.py page1.jpg page2.jpg

    # Using another model preset or custom model ID
    python scripts/spike_remito_vision.py --model claude page1.jpg
    python scripts/spike_remito_vision.py --model gpt-4o-mini page1.jpg
    python scripts/spike_remito_vision.py --model qwen page1.jpg

    # Save output to JSON
    python scripts/spike_remito_vision.py page1.jpg -o result.json

    # Test parser & rich output without an API key (mock mode)
    python scripts/spike_remito_vision.py --mock
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any

# Auto-bootstrap into project .venv if invoked with system/global python
_venv_python = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
if _venv_python.exists() and os.path.realpath(sys.executable) != os.path.realpath(
    _venv_python
):
    os.execv(str(_venv_python), [str(_venv_python)] + sys.argv)

import httpx  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

# Try loading .env if available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Try rich for colorful terminal output, fallback to plain text
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


# ==============================================================================
# Model Presets & Pricing
# ==============================================================================

MODEL_PRESETS: dict[str, str] = {
    # Primary workhorse (fastest, lowest cost, excellent Spanish OCR)
    "gemini": "google/gemini-2.5-flash",
    "gemini-flash": "google/gemini-2.5-flash",
    "gemini-lite": "google/gemini-2.5-flash-lite",
    "gemini-pro": "google/gemini-2.5-pro",
    # DeepSeek vision models
    "deepseek": "deepseek/deepseek-v4.1-flash",
    "deepseek-flash": "deepseek/deepseek-v4.1-flash",
    "deepseek-v4.1-flash": "deepseek/deepseek-v4.1-flash",
    # Anthropic models
    "claude": "anthropic/claude-sonnet-4.5",
    "sonnet": "anthropic/claude-sonnet-4.5",
    "haiku": "anthropic/claude-haiku-4.5",
    # OpenAI models
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    # Open source vision models
    "qwen": "qwen/qwen2.5-vl-72b-instruct",
}


def resolve_model_id(model_input: str) -> str:
    """Resolve preset alias or return custom model ID string."""
    key = model_input.lower().strip()
    if key in MODEL_PRESETS:
        return MODEL_PRESETS[key]
    for preset_key, preset_val in MODEL_PRESETS.items():
        if key == preset_key or key == preset_val.split("/")[-1].lower():
            return preset_val
    return model_input


# ==============================================================================
# Structured Output Pydantic Schemas
# ==============================================================================


class ExtractedLineItem(BaseModel):
    """Single printed line item extracted from the delivery receipt."""

    line_index: int = Field(description="0-based sequential line position")
    raw_description: str = Field(
        description=(
            "Full item text as printed (e.g. 'Barritas Almendra x 41 gr x 10 u')"
        )
    )
    quantity: int = Field(
        default=1,
        description="Wholesale package count as printed on receipt",
    )
    unit_cost: int = Field(
        default=0,
        description="Cost per wholesale package in whole ARS as printed",
    )
    line_total: int = Field(
        default=0,
        description="Line total in whole ARS as printed",
    )
    confidence: int = Field(
        default=90,
        description="Extraction confidence percentage (0-100)",
    )


class ExtractedFiscalInfo(BaseModel):
    """Fiscal totals and split information extracted from receipt header/footer."""

    subtotal: int | None = Field(
        default=None,
        description="Subtotal before tax/split (whole ARS)",
    )
    total: int | None = Field(
        default=None,
        description="Document grand total (whole ARS)",
    )
    discount_percentage: int | None = Field(
        default=None,
        description="Global discount percentage if printed (0-100)",
    )
    blanco_percentage: int | None = Field(
        default=None,
        description="Percentage billed formally con factura (e.g. 60)",
    )
    negro_percentage: int | None = Field(
        default=None,
        description="Percentage billed informally sin factura (e.g. 40)",
    )
    iva_percentage: int | None = Field(
        default=None,
        description="IVA rate printed on receipt (e.g. 21)",
    )


class RemitoVisionOutput(BaseModel):
    """Complete structured extraction from one or more receipt images."""

    supplier_name: str | None = Field(
        default=None,
        description=(
            "Distributor name from receipt header (e.g. 'New Day Distribuidora')"
        ),
    )
    remito_number: str | None = Field(
        default=None,
        description="Document / delivery note number (e.g. '0001-00045231')",
    )
    date_issued: str | None = Field(
        default=None,
        description="Date in ISO 8601 format (YYYY-MM-DD) if legible",
    )
    page_count: int = Field(default=1)
    items: list[ExtractedLineItem] = Field(default_factory=list)
    fiscal_info: ExtractedFiscalInfo | None = Field(default=None)
    overall_confidence: int = Field(
        default=85,
        description="Overall extraction confidence (0-100)",
    )
    extraction_notes: list[str] = Field(
        default_factory=list,
        description=(
            "Escape hatch: unmodeled surcharges (IIBB, flete), payment terms, "
            "container deposits, scan quality notes, or items not fitting the schema"
        ),
    )


# ==============================================================================
# System Prompt Tuning (Argentine Remito / Recibo X Domain)
# ==============================================================================

REMITO_EXTRACTION_SYSTEM_PROMPT = """\
You are an expert OCR and data extraction system specialized in Argentine commercial \
delivery receipts (Remitos, Recibos X, Liquidaciones de Distribución) for dietéticas \
and dietary food retail stores.

TASK: Extract clean, structured JSON from the provided receipt photo(s).

DOMAIN CONTEXT:
1. These are WHOLESALE delivery notes from distributors (e.g. New Day Distribuidora, \
   Distribuidora Patagonia, La Natural, etc.).
2. Items represent wholesale packaging: 'caja', 'pack', 'display', 'bolsa', 'kg', 'u'.
3. Descriptions frequently embed packaging specs, e.g.:
   - 'Barritas Almendra x 41 gr x 10 u (Integra)'
   - 'Yerba Kalena x 2 kg x 5 u'
   - 'Almendras Peladas Nonpareil x 10 kg'
4. Prices and totals are in whole Argentine Pesos (ARS). Never use decimals/cents.
5. Multi-page receipts: maintain sequential line_index across all pages.
   Consolidate into a single items list.

CRITICAL — PRINTED TEXT ONLY (IGNORE HANDWRITING):
Extract ONLY the original PRINTED text of the receipt.
Completely IGNORE all handwritten annotations, blue/black ballpoint pen marks,
checkmarks, ticks, crossed-out lines, or handwritten notes on the physical paper.
Do NOT attempt to read, transcribe, or detect handwriting.
Extract the original printed descriptions, quantities, and prices as originally printed.

EXTRACTION NOTES & ESCAPE HATCH (CRITICAL):
Use the `extraction_notes` array as an escape hatch to capture any receipt \
information that does not fit into standard line items or fiscal_info fields:
- Fiscal surcharges: Percepciones IIBB (Ingresos Brutos), Percepción IVA, etc.
- Logistics / Freight: Flete, costo de envío, seguro de mercadería.
- Commercial & payment terms: Descuento contado, recargo cta cte, plazos.
- Container deposits / returnables: Seña de cajones, pallets, envases.
- Data anomalies: Items with $0 cost (muestras / bonificaciones), unreadable text.

OUTPUT SPECIFICATION:
Return a single JSON object matching this schema exactly:
{
  "supplier_name": "string or null",
  "remito_number": "string or null",
  "date_issued": "YYYY-MM-DD or null",
  "page_count": int,
  "items": [
    {
      "line_index": int,
      "raw_description": "string",
      "quantity": int,
      "unit_cost": int,
      "line_total": int,
      "confidence": int (0-100)
    }
  ],
  "fiscal_info": {
    "subtotal": int or null,
    "total": int or null,
    "discount_percentage": int or null,
    "blanco_percentage": int or null,
    "negro_percentage": int or null,
    "iva_percentage": int or null
  },
  "overall_confidence": int (0-100),
  "extraction_notes": ["string"]
}

STRICT RULE: Return ONLY the JSON object. Do not wrap in markdown code blocks. \
Do not output conversational preamble or postscript.\
"""


# ==============================================================================
# Image Encoding & Preprocessing
# ==============================================================================


def encode_image_to_data_uri(image_path: Path) -> str:
    """Read an image file and convert to base64 data URI."""
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/jpeg"

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")

    return f"data:{mime_type};base64,{encoded}"


# ==============================================================================
# OpenRouter API Client
# ==============================================================================


async def call_openrouter_vision(
    image_paths: list[Path],
    model: str,
    api_key: str,
    temperature: float = 0.1,
    max_tokens: int = 8192,
    debug: bool = False,
) -> tuple[RemitoVisionOutput, dict[str, Any], float]:
    """Call OpenRouter Chat Completions API with image payload and structured prompt.

    Returns:
        tuple of (parsed_output, usage_dict, elapsed_seconds)
    """
    data_uris = [encode_image_to_data_uri(p) for p in image_paths]

    # Build multimodal content payload
    content_blocks: list[dict[str, Any]] = []
    for i, uri in enumerate(data_uris):
        if len(data_uris) > 1:
            content_blocks.append(
                {
                    "type": "text",
                    "text": (
                        f"--- Receipt Page {i + 1} of {len(data_uris)} "
                        f"({image_paths[i].name}) ---"
                    ),
                }
            )
        content_blocks.append(
            {
                "type": "image_url",
                "image_url": {"url": uri},
            }
        )

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": REMITO_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": content_blocks},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Only pass response_format for models with proven JSON-mode support.
    # Many OpenRouter models (DeepSeek, Claude, open-source) return null content
    # or fail when response_format is forced.
    if any(p in model.lower() for p in ("openai/", "gpt-", "google/", "gemini-")):
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://vitalcer.app",
        "X-Title": "Vitalcer Remito Ingestion Spike",
        "Content-Type": "application/json",
    }

    start_time = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
        )
    elapsed = time.perf_counter() - start_time

    if response.status_code != 200:
        error_detail = response.text
        try:
            error_json = response.json()
            error_detail = error_json.get("error", {}).get("message", error_detail)
        except Exception:
            pass
        if response.status_code == 429:
            raise RuntimeError(
                f"OpenRouter Rate Limit Exceeded (HTTP 429): {error_detail}\n"
                "Tip: If you are using a ':free' model, free tier endpoints "
                "are frequently congested. Use a standard model like 'gemini' "
                "(google/gemini-2.0-flash-001) which costs ~$0.001 per scan."
            )
        raise RuntimeError(
            f"OpenRouter API error (HTTP {response.status_code}): {error_detail}"
        )

    res_json = response.json()
    if debug:
        print("\n--- [DEBUG] Full OpenRouter Response JSON ---")
        print(json.dumps(res_json, indent=2))
        print("---------------------------------------------\n")

    choices = res_json.get("choices")
    if not choices:
        raise RuntimeError(
            f"OpenRouter returned no choices: {json.dumps(res_json, indent=2)}"
        )

    choice = choices[0]
    message = choice.get("message", {})
    raw_content = message.get("content")

    # If content is null, check if reasoning/thinking model placed output in reasoning
    if not raw_content:
        raw_content = message.get("reasoning_content") or message.get("reasoning")

    # If still empty or null, provide a clear diagnostic error
    if not raw_content:
        finish_reason = choice.get("finish_reason")
        refusal = message.get("refusal")
        err_msg = (
            f"Model '{model}' returned empty content "
            f"(finish_reason: '{finish_reason}').\n"
        )
        if refusal:
            err_msg += f"Model Refusal: {refusal}\n"
        if finish_reason == "length":
            err_msg += (
                "The model ran out of tokens before writing the JSON response.\n"
                "Try increasing --max-tokens (e.g. --max-tokens 16384).\n"
            )
        err_msg += f"Full API response:\n{json.dumps(res_json, indent=2)}"
        raise RuntimeError(err_msg)

    # Locate outermost JSON object {...}
    start_brace = raw_content.find("{")
    end_brace = raw_content.rfind("}")
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        cleaned_content = raw_content[start_brace : end_brace + 1].strip()
    else:
        cleaned_content = raw_content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:]
        elif cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:]
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3]
        cleaned_content = cleaned_content.strip()

    try:
        parsed = RemitoVisionOutput.model_validate_json(cleaned_content)
    except Exception as err:
        raise RuntimeError(
            f"Failed to parse model output into RemitoVisionOutput schema: {err}\n"
            f"Raw model response was:\n{raw_content}"
        ) from err

    usage = res_json.get("usage", {})
    return parsed, usage, elapsed


# ==============================================================================
# Mock Data Generator (for offline testing)
# ==============================================================================


def get_mock_output() -> RemitoVisionOutput:
    """Return realistic mock RemitoVisionOutput representing a New Day delivery note."""
    return RemitoVisionOutput(
        supplier_name="New Day Distribuidora",
        remito_number="0001-00045231",
        date_issued="2026-10-08",
        page_count=2,
        items=[
            ExtractedLineItem(
                line_index=0,
                raw_description="Barritas Almendra x 41 gr x 10 u (Integra)",
                quantity=1,
                unit_cost=5000,
                line_total=5000,
                confidence=95,
            ),
            ExtractedLineItem(
                line_index=1,
                raw_description="Yerba Kalena Despalada x 2 kg x 5 u",
                quantity=2,
                unit_cost=12000,
                line_total=24000,
                confidence=90,
            ),
            ExtractedLineItem(
                line_index=2,
                raw_description="Granola Tradicional Crocante x 5 kg",
                quantity=1,
                unit_cost=18500,
                line_total=18500,
                confidence=92,
            ),
            ExtractedLineItem(
                line_index=3,
                raw_description="Semillas de Chía Premium x 10 kg",
                quantity=1,
                unit_cost=32000,
                line_total=32000,
                confidence=94,
            ),
            ExtractedLineItem(
                line_index=4,
                raw_description="Té Verde con Jazmín en Hebras x 250 gr x 6 u",
                quantity=1,
                unit_cost=7800,
                line_total=7800,
                confidence=88,
            ),
        ],
        fiscal_info=ExtractedFiscalInfo(
            subtotal=87300,
            total=97776,
            discount_percentage=0,
            blanco_percentage=60,
            negro_percentage=40,
            iva_percentage=21,
        ),
        overall_confidence=92,
        extraction_notes=[
            "Página 1 y 2 procesadas correctamente (solo texto impreso).",
            "Anotaciones manuscritas ignoradas según especificación.",
        ],
    )


# ==============================================================================
# Reporting & Output Formatting
# ==============================================================================


def print_rich_report(
    result: RemitoVisionOutput,
    model: str,
    usage: dict[str, Any],
    elapsed: float,
) -> None:
    """Render extracted delivery note data using rich panels and tables."""
    if console is None:
        print_plain_report(result, model, usage, elapsed)
        return

    # Summary panel
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

    conf_color = "green" if result.overall_confidence >= 80 else "yellow"
    info_text = (
        f"[bold cyan]Proveedor:[/bold cyan] {result.supplier_name}  |  "
        f"[bold cyan]Remito N°:[/bold cyan] {result.remito_number or 'N/A'}  |  "
        f"[bold cyan]Fecha:[/bold cyan] {result.date_issued or 'N/A'}  |  "
        f"[bold cyan]Páginas:[/bold cyan] {result.page_count}\n"
        f"[bold cyan]Modelo:[/bold cyan] {model}  |  "
        f"[bold cyan]Tiempo:[/bold cyan] {elapsed:.2f}s  |  "
        f"[bold cyan]Tokens:[/bold cyan] {total_tokens:,} "
        f"(in: {prompt_tokens:,}, out: {completion_tokens:,})  |  "
        f"[bold cyan]Confianza:[/bold cyan] "
        f"[{conf_color}]{result.overall_confidence}%[/]"
    )
    console.print(
        Panel(
            info_text,
            title="[bold green]📦 Remito Vision Extraction Spike[/bold green]",
            border_style="green",
        )
    )

    # Line items table
    table = Table(title=f"Extracted Line Items ({len(result.items)} items)")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Descripción / Packaging Impreso", style="white")
    table.add_column("Cant.", justify="right")
    table.add_column("Precio Unit.", justify="right")
    table.add_column("Total Línea", justify="right")
    table.add_column("Conf.", justify="center")

    computed_sum = 0
    for idx, item in enumerate(result.items, start=1):
        computed_sum += item.line_total
        conf_badge = (
            f"[green]{item.confidence}%[/green]"
            if item.confidence >= 80
            else f"[yellow]{item.confidence}%[/yellow]"
        )
        table.add_row(
            str(idx),
            item.raw_description,
            str(item.quantity),
            f"${item.unit_cost:,} ARS",
            f"${item.line_total:,} ARS",
            conf_badge,
        )

    console.print(table)

    # Fiscal & reconciliation summary
    f = result.fiscal_info
    if f:
        reconcile_table = Table(
            title="Fiscal Split & Mathematical Checksum", show_header=False
        )
        reconcile_table.add_column("Concept", style="dim")
        reconcile_table.add_column("Value", style="bold")

        reconcile_table.add_row("Suma de Líneas Extraídas:", f"${computed_sum:,} ARS")
        if f.subtotal:
            reconcile_table.add_row("Subtotal Impreso:", f"${f.subtotal:,} ARS")
        if f.total:
            reconcile_table.add_row("Total Documento Impreso:", f"${f.total:,} ARS")

        # Checksum alert
        if f.total and f.total > 0:
            diff = abs(computed_sum - f.total)
            if diff <= max(f.total // 100, 1):
                reconcile_table.add_row(
                    "Conciliación Matemática:",
                    "[green]✓ Coincide (dentro del 1% de tolerancia)[/green]",
                )
            else:
                reconcile_table.add_row(
                    "Conciliación Matemática:",
                    (
                        f"[bold red]⚠ Discrepancia de ${diff:,} ARS "
                        f"entre líneas y total[/bold red]"
                    ),
                )

        if f.blanco_percentage and f.negro_percentage:
            iva_str = f"{f.iva_percentage or 21}%"
            reconcile_table.add_row(
                "Split Fiscal Detectado:",
                f"{f.blanco_percentage}% Blanco (con IVA {iva_str}) / "
                f"{f.negro_percentage}% Negro",
            )

        console.print(reconcile_table)

    # Extraction notes
    if result.extraction_notes:
        console.print(
            Panel(
                "\n".join(f"• {n}" for n in result.extraction_notes),
                title="[yellow]Notas de Extracción[/yellow]",
                border_style="yellow",
            )
        )


def print_plain_report(
    result: RemitoVisionOutput,
    model: str,
    usage: dict[str, Any],
    elapsed: float,
) -> None:
    """Fallback plain text renderer if rich is not installed."""
    print("=" * 70)
    print("REMITO VISION EXTRACTION SPIKE")
    print("=" * 70)
    print(f"Proveedor:         {result.supplier_name}")
    print(f"Remito N°:         {result.remito_number or 'N/A'}")
    print(f"Fecha:             {result.date_issued or 'N/A'}")
    print(f"Modelo:            {model} ({elapsed:.2f}s)")
    print(
        f"{'#':<3} {'Descripción':<36} {'Cant':<5} {'Precio':<10} "
        f"{'Total':<10} {'Conf':<6}"
    )
    print("-" * 74)
    for idx, it in enumerate(result.items, start=1):
        print(
            f"{idx:<3} {it.raw_description[:40]:<42} {it.quantity:<5} "
            f"${it.unit_cost:<9} ${it.line_total:<9} {it.confidence}%"
        )
    print("=" * 78)


# ==============================================================================
# CLI Main
# ==============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Vision Spike: Extract structured data from delivery receipts "
            "via OpenRouter."
        )
    )
    parser.add_argument(
        "images",
        nargs="*",
        type=Path,
        help="One or more image files (JPEG, PNG, WebP) of receipt pages.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="gemini",
        help=(
            "Model identifier or preset alias. Available presets: "
            + ", ".join(f"'{k}'" for k in MODEL_PRESETS.keys())
            + ". Default: 'gemini' (google/gemini-2.0-flash-001)."
        ),
    )
    parser.add_argument(
        "-k",
        "--api-key",
        default=os.getenv("OPENROUTER_API_KEY"),
        help=(
            "OpenRouter API key (defaults to OPENROUTER_API_KEY environment variable)."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to save raw JSON output.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw JSON to stdout.",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=0.1,
        help="LLM temperature (default: 0.1 for deterministic extraction).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help=(
            "Run in mock mode with sample New Day delivery note "
            "(no API key or images required)."
        ),
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=8192,
        help="Maximum completion tokens limit (default: 8192).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print raw API response payload for troubleshooting.",
    )

    args = parser.parse_args()

    # Mock mode
    if args.mock or (not args.images and not args.api_key):
        if not args.mock:
            print(
                "Note: No images or API key provided. Running with sample mock data.\n"
            )
        model_id = resolve_model_id(args.model)
        result = get_mock_output()
        usage = {"prompt_tokens": 1250, "completion_tokens": 420}
        elapsed = 1.85

        if args.raw:
            print(result.model_dump_json(indent=2))
        else:
            if HAS_RICH:
                print_rich_report(result, model_id, usage, elapsed)
            else:
                print_plain_report(result, model_id, usage, elapsed)

        if args.output:
            args.output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            print(f"\nWrote JSON to {args.output}")
        return

    # Validate inputs
    if not args.images:
        print(
            "Error: Please provide at least one image file, or use --mock.",
            file=sys.stderr,
        )
        sys.exit(1)

    for img in args.images:
        if not img.exists():
            print(f"Error: Image file not found: {img}", file=sys.stderr)
            sys.exit(1)

    if not args.api_key:
        print(
            "Error: OpenRouter API key required. Set OPENROUTER_API_KEY in "
            "your environment, add it to .env, or pass --api-key <key>.",
            file=sys.stderr,
        )
        sys.exit(1)

    model_id = resolve_model_id(args.model)
    print(f"Processing {len(args.images)} page(s) with model '{model_id}'...")

    import asyncio

    try:
        result, usage, elapsed = asyncio.run(
            call_openrouter_vision(
                args.images,
                model=model_id,
                api_key=args.api_key,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                debug=args.debug,
            )
        )
    except Exception as e:
        print(f"\nExtraction failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Render results
    if args.raw:
        print(result.model_dump_json(indent=2))
    else:
        if HAS_RICH:
            print_rich_report(result, model_id, usage, elapsed)
        else:
            print_plain_report(result, model_id, usage, elapsed)

    if args.output:
        args.output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print(f"\nWrote JSON output to {args.output}")


if __name__ == "__main__":
    main()
