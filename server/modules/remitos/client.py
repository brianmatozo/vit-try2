import asyncio
import re
from typing import Any

import httpx

from server.core.config import settings
from server.core.exceptions import VisionExtractionError, VisionGatewayError
from server.modules.remitos.preprocessor import (
    encode_image_bytes,
    preprocess_image_bytes,
    preprocess_image_data_uri,
)
from server.modules.remitos.prompts import (
    FALLBACK_MODEL,
    PRIMARY_MODEL,
    REMITO_EXTRACTION_SYSTEM_PROMPT,
)
from server.modules.remitos.schemas import RemitoVisionOutput

__all__ = [
    "FALLBACK_MODEL",
    "PRIMARY_MODEL",
    "REMITO_EXTRACTION_SYSTEM_PROMPT",
    "encode_image_bytes",
    "extract_remito",
    "preprocess_image_bytes",
    "preprocess_image_data_uri",
]


def _clean_json_markdown(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    return m.group(1).strip() if m else text.strip()


async def _execute_chat_completion_with_retry(
    client: httpx.AsyncClient, payload: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Execute OpenRouter chat completion with 429 backoff and 5xx retries."""
    max_429, backoff = 3, 1.0
    for attempt in range(max_429 + 1):
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
            if attempt < max_429:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)
                continue
            raise VisionGatewayError("Límite de tasa excedido en OpenRouter (429).")
        if resp.status_code in (500, 502, 503):
            if attempt == 0:
                await asyncio.sleep(2.0)
                continue
            raise VisionGatewayError(
                f"Servicio OpenRouter no disponible (HTTP {resp.status_code})."
            )
        raise VisionGatewayError(f"Error OpenRouter: HTTP {resp.status_code}")
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
    if not (key := api_key or settings.openrouter_api_key):
        raise ValueError("OPENROUTER_API_KEY is not configured")

    selected = model or settings.openrouter_primary_model or PRIMARY_MODEL
    content: list[dict[str, Any]] = []
    for i, uri in enumerate(image_data_uris):
        if len(image_data_uris) > 1:
            content.append({"type": "text", "text": f"--- Page {i + 1} ---"})
        content.append({"type": "image_url", "image_url": {"url": uri}})

    payload: dict[str, Any] = {
        "model": selected,
        "messages": [
            {"role": "system", "content": REMITO_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
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
        raw = data["choices"][0]["message"]["content"]
        try:
            result = RemitoVisionOutput.model_validate_json(_clean_json_markdown(raw))
        except Exception:
            retry_msgs = payload["messages"] + [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        "Return valid JSON matching RemitoVisionOutput strictly."
                    ),
                },
            ]
            retry = await _execute_chat_completion_with_retry(
                client, {**payload, "messages": retry_msgs}, headers
            )
            try:
                result = RemitoVisionOutput.model_validate_json(
                    _clean_json_markdown(retry["choices"][0]["message"]["content"])
                )
            except Exception as err:
                raise VisionExtractionError(
                    "No se pudo interpretar el formato del comprobante."
                ) from err

    if result.overall_confidence < 50 and selected == PRIMARY_MODEL:
        fallback = settings.openrouter_fallback_model or FALLBACK_MODEL
        return await extract_remito(image_data_uris, model=fallback, api_key=key)
    return result
