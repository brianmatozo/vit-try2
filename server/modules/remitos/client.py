import base64
import re
from typing import Any

import httpx

from server.core.config import settings
from server.modules.remitos.schemas import RemitoVisionOutput

PRIMARY_MODEL = "google/gemini-2.0-flash-001"
FALLBACK_MODEL = "anthropic/claude-3.5-sonnet"

REMITO_EXTRACTION_SYSTEM_PROMPT = """\
You are an expert data extraction system specialized in Argentine commercial \
delivery receipts (Remitos, Recibos X, Liquidaciones) from food distributors.

TASK: Extract structured data from the provided receipt photo(s).
CRITICAL EXTRACTION RULE — IGNORE HANDWRITING:
- Focus EXCLUSIVELY on extracting the original PRINTED text of the receipt.
- Completely IGNORE all handwritten pen marks, ticks, or handwritten notes.
- All monetary values must be integers (whole ARS, no decimals).

OUTPUT: Return a single JSON object matching the RemitoVisionOutput schema.\
"""


def encode_image_bytes(raw_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Encode raw image bytes to base64 data URI."""
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:{mime_type};base64,{b64}"


def _clean_json_markdown(text: str) -> str:
    """Strip ```json ... ``` code blocks if present."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    return match.group(1).strip() if match else text.strip()


async def extract_remito(
    image_data_uris: list[str],
    model: str | None = None,
    mock_response: RemitoVisionOutput | None = None,
    api_key: str | None = None,
) -> RemitoVisionOutput:
    """Extract structured data from receipt images via OpenRouter or mock fixture."""
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

    payload: dict[str, Any] = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": REMITO_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": content_blocks},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://vitalcer.app",
        "X-OpenRouter-Title": "Vitalcer Remito Ingestion",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    raw_text = data["choices"][0]["message"]["content"]
    cleaned = _clean_json_markdown(raw_text)
    result = RemitoVisionOutput.model_validate_json(cleaned)

    # Fallback retry if low confidence
    if result.overall_confidence < 50 and selected_model == PRIMARY_MODEL:
        fallback = settings.openrouter_fallback_model or FALLBACK_MODEL
        return await extract_remito(image_data_uris, model=fallback, api_key=key)

    return result
