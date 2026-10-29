import asyncio
import base64
import io
import re
from typing import Any

import httpx
from PIL import Image, ImageOps

from server.core.config import settings
from server.core.exceptions import (
    CorruptImageError,
    VisionExtractionError,
    VisionGatewayError,
)
from server.modules.remitos.schemas import RemitoVisionOutput

PRIMARY_MODEL = "google/gemini-2.0-flash-001"
FALLBACK_MODEL = "anthropic/claude-3.5-sonnet"
MAX_DIMENSION = 2048
WEBP_QUALITY = 85

REMITO_EXTRACTION_SYSTEM_PROMPT = """\
You are an expert data extraction system specialized in Argentine commercial \
delivery receipts (Remitos, Recibos X, Liquidaciones) from food distributors.

TASK: Extract structured printed data from the delivery receipt photo(s).

MULTI-PAGE RECEIPTS & ORDERING:
- Receipts may span multiple pages (e.g. "Pag 1/2", "Hoja 1 de 2").
- Extract items from ALL pages sequentially into a single unified items array.
- Assign sequential 0-based line_index continuing across pages.
- Header info (supplier, remito number, date) is deduplicated from the 1st page.
- Document totals must be extracted from the final summary footer.

CRITICAL EXTRACTION RULE — IGNORE HANDWRITING:
- Focus EXCLUSIVELY on extracting original PRINTED text.
- Completely IGNORE all handwritten ink marks, ticks, pen scribbles, or checks.
- All monetary values must be integers (whole ARS, no decimals).

OUTPUT: Return a single JSON object matching the RemitoVisionOutput schema.\
"""


def preprocess_image_bytes(raw_bytes: bytes) -> str:
    """Validate image bytes with Pillow, fix EXIF orientation, and encode WebP."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()
        img = Image.open(io.BytesIO(raw_bytes))
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        raise CorruptImageError(
            "Archivo de imagen corrupto o formato no soportado."
        ) from e

    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=WEBP_QUALITY)
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{b64}"


def preprocess_image_data_uri(data_uri: str) -> str:
    """Preprocess image data URI: validate corruption, resize, and return WebP."""
    if not data_uri.startswith("data:"):
        raise CorruptImageError("Formato de URI de imagen no válido.")
    try:
        _, b64_data = data_uri.split(",", 1)
        raw_bytes = base64.b64decode(b64_data)
    except Exception as e:
        raise CorruptImageError(
            "Archivo de imagen corrupto o formato no soportado."
        ) from e
    return preprocess_image_bytes(raw_bytes)


def encode_image_bytes(raw_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Encode raw image bytes to base64 data URI (preprocessed via WebP)."""
    try:
        return preprocess_image_bytes(raw_bytes)
    except CorruptImageError:
        b64 = base64.b64encode(raw_bytes).decode("ascii")
        return f"data:{mime_type};base64,{b64}"


def _clean_json_markdown(text: str) -> str:
    """Strip ```json ... ``` code blocks if present."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    return match.group(1).strip() if match else text.strip()


async def _execute_chat_completion_with_retry(
    client: httpx.AsyncClient, payload: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Execute OpenRouter chat completion with 429 backoff and 5xx retries."""
    max_429_retries = 3
    backoff_seconds = 1.0

    for attempt in range(max_429_retries + 1):
        try:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as err:
            raise VisionGatewayError(
                "Tiempo de espera agotado al conectar con OpenRouter."
            ) from err

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 401:
            raise VisionGatewayError("OpenRouter API key inválida o no autorizada.")

        if resp.status_code == 429:
            if attempt < max_429_retries:
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 30.0)
                continue
            raise VisionGatewayError(
                "Límite de tasa excedido en OpenRouter (429 Too Many Requests)."
            )

        if resp.status_code in (500, 502, 503):
            if attempt == 0:
                await asyncio.sleep(2.0)
                continue
            raise VisionGatewayError(
                f"Servicio OpenRouter no disponible (HTTP {resp.status_code})."
            )

        raise VisionGatewayError(
            f"Error devuelto por OpenRouter: HTTP {resp.status_code}"
        )

    raise VisionGatewayError("Número máximo de reintentos con OpenRouter excedido.")


async def extract_remito(
    image_data_uris: list[str],
    model: str | None = None,
    mock_response: RemitoVisionOutput | None = None,
    api_key: str | None = None,
) -> RemitoVisionOutput:
    """Extract structured data from receipt images via OpenRouter with retries."""
    if mock_response is not None:
        return mock_response

    key = api_key or settings.openrouter_api_key
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not configured")

    selected_model = model or settings.openrouter_primary_model or PRIMARY_MODEL
    content_blocks: list[dict[str, Any]] = []
    for i, uri in enumerate(image_data_uris):
        if len(image_data_uris) > 1:
            content_blocks.append({"type": "text", "text": f"--- Page {i + 1} ---"})
        content_blocks.append({"type": "image_url", "image_url": {"url": uri}})

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": REMITO_EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": content_blocks},
    ]

    payload: dict[str, Any] = {
        "model": selected_model,
        "messages": messages,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://vitalcer.app",
        "X-OpenRouter-Title": "Vitalcer Remito Ingestion",
    }

    async with httpx.AsyncClient(timeout=35.0) as client:
        data = await _execute_chat_completion_with_retry(client, payload, headers)

        raw_text = data["choices"][0]["message"]["content"]
        cleaned = _clean_json_markdown(raw_text)
        try:
            result = RemitoVisionOutput.model_validate_json(cleaned)
        except Exception:
            messages.append({"role": "assistant", "content": raw_text})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Return valid JSON matching RemitoVisionOutput strictly."
                    ),
                }
            )
            retry_data = await _execute_chat_completion_with_retry(
                client, payload, headers
            )
            retry_text = retry_data["choices"][0]["message"]["content"]
            try:
                result = RemitoVisionOutput.model_validate_json(
                    _clean_json_markdown(retry_text)
                )
            except Exception as err:
                raise VisionExtractionError(
                    "No se pudo interpretar el formato del comprobante."
                ) from err

    # Fallback retry if overall confidence too low
    if result.overall_confidence < 50 and selected_model == PRIMARY_MODEL:
        fallback = settings.openrouter_fallback_model or FALLBACK_MODEL
        return await extract_remito(image_data_uris, model=fallback, api_key=key)

    return result
