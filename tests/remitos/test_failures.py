import base64
import io
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.exceptions import (
    CorruptImageError,
    RemitoConflictError,
    VisionGatewayError,
)
from server.modules.catalog.models import Product, ProductType
from server.modules.remitos.client import (
    extract_remito,
    preprocess_image_bytes,
    preprocess_image_data_uri,
)
from server.modules.remitos.models import RemitoStatus
from server.modules.remitos.schemas import ExtractedLineItem, RemitoVisionOutput
from server.modules.remitos.service import confirm_remito, scan_and_stage_remito


def test_corrupt_image_preprocessing_raises():
    corrupt_bytes = b"not-a-valid-image-stream"
    with pytest.raises(CorruptImageError):
        preprocess_image_bytes(corrupt_bytes)

    with pytest.raises(CorruptImageError):
        preprocess_image_data_uri("data:image/jpeg;base64,not-base64-data!!")

    with pytest.raises(CorruptImageError):
        preprocess_image_data_uri("invalid-uri-no-data-prefix")


def test_valid_image_preprocessing_downscale():
    # Create large 3000x1000 image
    img = Image.new("RGB", (3000, 1000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    data_uri = preprocess_image_bytes(buf.getvalue())

    assert data_uri.startswith("data:image/webp;base64,")
    _, b64 = data_uri.split(",", 1)
    out_img = Image.open(io.BytesIO(base64.b64decode(b64)))
    assert max(out_img.size) <= 2048


def test_corrupt_image_endpoint_returns_400(client: TestClient):
    resp = client.post(
        "/api/v1/remitos/scan-images",
        json={"mock": False, "images": ["data:image/jpeg;base64,invalid-corrupt-data"]},
    )
    assert resp.status_code == 400
    assert "Archivo de imagen corrupto" in resp.json()["detail"]


@pytest.mark.anyio
async def test_openrouter_api_401_raises_gateway_error():
    mock_resp = httpx.Response(401, json={"error": "Unauthorized"})
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(VisionGatewayError, match="API key inválida"):
            await extract_remito(["data:image/webp;base64,fake"], api_key="bad-key")


@pytest.mark.anyio
async def test_openrouter_api_500_retries_and_raises():
    mock_resp = httpx.Response(500, text="Internal Server Error")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(VisionGatewayError, match="no disponible"):
            await extract_remito(["data:image/webp;base64,fake"], api_key="test-key")
        assert mock_post.call_count == 2  # Retried once after 2s


@pytest.mark.anyio
async def test_double_commit_prevention_raises_conflict(async_session: AsyncSession):
    prod = Product(
        sku="BAR-LADDU-99",
        name="Barrita Laddu Double Commit",
        unit_price=2000,
        current_stock=10,
        product_type=ProductType.DISCRETE,
    )
    async_session.add(prod)
    await async_session.commit()

    vision = RemitoVisionOutput(
        supplier_name="New Day",
        remito_number="0001-9999",
        items=[
            ExtractedLineItem(
                line_index=0,
                raw_description="Barritas Laddu x 12 u",
                quantity=1,
                unit_cost=10000,
                line_total=10000,
            )
        ],
    )
    staged = await scan_and_stage_remito(async_session, vision)
    assert staged.id is not None
    staged.items[0].product_id = prod.id
    staged.items[0].quantity_to_commit = 12
    await async_session.commit()

    # First confirm succeeds
    confirmed = await confirm_remito(async_session, staged.id)
    assert confirmed.status == RemitoStatus.COMMITTED

    # Second confirm must fail with RemitoConflictError
    with pytest.raises(RemitoConflictError, match="expected staged"):
        await confirm_remito(async_session, staged.id)
