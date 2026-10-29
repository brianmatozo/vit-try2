import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from server.core.config import settings
from server.core.dependencies import get_async_db
from server.core.exceptions import EntityNotFoundError
from server.modules.remitos.client import (
    extract_remito,
    preprocess_image_data_uri,
)
from server.modules.remitos.models import (
    Remito,
    RemitoStatus,
    SupplierProductMapping,
)
from server.modules.remitos.schemas import (
    ExtractedLineItem,
    RemitoConfigDTO,
    RemitoConfigUpdate,
    RemitoHeaderUpdate,
    RemitoItemResponse,
    RemitoItemUpdate,
    RemitoResponse,
    RemitoVisionOutput,
    ScanImagesRequest,
    SupplierMappingResponse,
)
from server.modules.remitos.service import (
    confirm_remito,
    reject_remito,
    scan_and_stage_remito,
    update_remito_header,
    update_remito_item,
)

router = APIRouter(tags=["remitos"])


@router.get("/remitos/config", response_model=RemitoConfigDTO)
async def get_config():
    """Get runtime configuration for OpenRouter vision extraction."""
    return RemitoConfigDTO(
        has_api_key=bool(settings.openrouter_api_key),
        primary_model=settings.openrouter_primary_model,
        fallback_model=settings.openrouter_fallback_model,
    )


@router.post("/remitos/config", response_model=RemitoConfigDTO)
async def update_config(req: RemitoConfigUpdate):
    """Update runtime configuration for OpenRouter vision extraction."""
    if req.api_key is not None:
        settings.openrouter_api_key = req.api_key
    if req.primary_model is not None:
        settings.openrouter_primary_model = req.primary_model
    return RemitoConfigDTO(
        has_api_key=bool(settings.openrouter_api_key),
        primary_model=settings.openrouter_primary_model,
        fallback_model=settings.openrouter_fallback_model,
    )


@router.post(
    "/remitos/scan-images",
    response_model=RemitoResponse,
    status_code=201,
)
async def scan_images(
    req: ScanImagesRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """Scan receipt images and stage delivery note."""
    processed_images: list[str] = []
    for img in req.images:
        if not req.mock:
            processed_images.append(preprocess_image_data_uri(img))
        else:
            processed_images.append(img)

    if req.mock or not (req.api_key or settings.openrouter_api_key):
        vision = RemitoVisionOutput(
            supplier_name=req.supplier_name or "Distribuidora New Day",
            remito_number=f"R-{datetime.now().strftime('%m%d-%H%M')}",
            page_count=len(processed_images) or 1,
            items=[
                ExtractedLineItem(
                    line_index=0,
                    raw_description="Barritas Almendra x 41 gr x 10 u",
                    quantity=2,
                    unit_cost=5000,
                    line_total=10000,
                    confidence=95,
                ),
                ExtractedLineItem(
                    line_index=1,
                    raw_description="Yerba Kalena x 2 kg x 5 u",
                    quantity=3,
                    unit_cost=12000,
                    line_total=36000,
                    confidence=88,
                ),
            ],
            overall_confidence=92,
        )
    else:
        vision = await extract_remito(
            image_data_uris=processed_images,
            model=req.model,
            api_key=req.api_key,
        )

    img_json = json.dumps(processed_images) if processed_images else None
    return await scan_and_stage_remito(
        db=db,
        vision=vision,
        image_paths=img_json,
        blanco_bps=req.blanco_pct * 100,
        negro_bps=req.negro_pct * 100,
        iva_rate_bps=req.iva_pct * 100,
    )


@router.patch("/remitos/{id}", response_model=RemitoResponse)
async def patch_remito(
    id: int, req: RemitoHeaderUpdate, db: AsyncSession = Depends(get_async_db)
):
    """Update remito header fiscal split or notes and recalculate unit costs."""
    return await update_remito_header(db=db, remito_id=id, req=req)


@router.post(
    "/remitos/scan-and-stage",
    response_model=RemitoResponse,
    status_code=201,
)
async def scan_and_stage(
    vision: RemitoVisionOutput,
    blanco_pct: int = 60,
    negro_pct: int = 40,
    iva_pct: int = 21,
    db: AsyncSession = Depends(get_async_db),
):
    """Stage an extracted remito payload for clerk audit and matching."""
    return await scan_and_stage_remito(
        db=db,
        vision=vision,
        blanco_bps=blanco_pct * 100,
        negro_bps=negro_pct * 100,
        iva_rate_bps=iva_pct * 100,
    )


@router.get("/remitos", response_model=list[RemitoResponse])
async def list_remitos(
    status: RemitoStatus | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
):
    """List remitos with optional status filter."""
    stmt = select(Remito).offset(offset).limit(limit)
    if status:
        stmt = stmt.where(Remito.status == status)
    return (await db.scalars(stmt)).all()


@router.get("/remitos/{id}", response_model=RemitoResponse)
async def get_remito(id: int, db: AsyncSession = Depends(get_async_db)):
    """Get single remito detail with items."""
    remito = await db.get(Remito, id)
    if not remito:
        raise EntityNotFoundError("Remito", id)
    return remito


@router.put("/remitos/{id}/items/{item_id}", response_model=RemitoItemResponse)
async def update_item(
    id: int,
    item_id: int,
    req: RemitoItemUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    """Inline edit a staged remito line item."""
    return await update_remito_item(db=db, remito_id=id, item_id=item_id, req=req)


@router.post("/remitos/{id}/confirm", response_model=RemitoResponse)
async def confirm(id: int, db: AsyncSession = Depends(get_async_db)):
    """Atomic double-entry stock commit and alias dictionary caching."""
    return await confirm_remito(db=db, remito_id=id)


@router.post("/remitos/{id}/reject", response_model=RemitoResponse)
async def reject(id: int, db: AsyncSession = Depends(get_async_db)):
    """Discard a staged delivery note."""
    return await reject_remito(db=db, remito_id=id)


@router.get(
    "/supplier-mappings",
    response_model=list[SupplierMappingResponse],
)
async def list_supplier_mappings(
    supplier: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_async_db),
):
    """List cached supplier-to-product alias mappings."""
    stmt = select(SupplierProductMapping).limit(limit)
    if supplier:
        stmt = stmt.where(
            col(SupplierProductMapping.supplier_name).ilike(f"%{supplier}%")
        )
    return (await db.scalars(stmt)).all()


@router.delete("/supplier-mappings/{id}", status_code=204)
async def delete_supplier_mapping(id: int, db: AsyncSession = Depends(get_async_db)):
    """Delete a cached alias dictionary entry."""
    mapping = await db.get(SupplierProductMapping, id)
    if not mapping:
        raise EntityNotFoundError("SupplierProductMapping", id)
    await db.delete(mapping)
    await db.commit()
