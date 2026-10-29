import json

from fastapi import APIRouter, Depends, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from server.core.config import settings
from server.core.dependencies import get_async_db
from server.core.exceptions import EntityNotFoundError
from server.modules.remitos.client import (
    extract_remito,
    preprocess_image_data_uri,
)
from server.modules.remitos.config_router import router as config_router
from server.modules.remitos.mappings_router import router as mappings_router
from server.modules.remitos.models import Remito, RemitoStatus
from server.modules.remitos.schemas import (
    RemitoHeaderUpdate,
    RemitoItemResponse,
    RemitoItemUpdate,
    RemitoResponse,
    RemitoVisionOutput,
    ScanImagesRequest,
)
from server.modules.remitos.service import (
    confirm_remito,
    reject_remito,
    scan_and_stage_remito,
    update_remito_header,
    update_remito_item,
)
from server.modules.remitos.staging import create_mock_vision

router = APIRouter(tags=["remitos"])
router.include_router(mappings_router)
router.include_router(config_router)


@router.post("/remitos/scan-images", response_model=RemitoResponse, status_code=201)
async def scan_images(req: ScanImagesRequest, db: AsyncSession = Depends(get_async_db)):
    imgs = [img if req.mock else preprocess_image_data_uri(img) for img in req.images]
    if req.mock or not (req.api_key or settings.openrouter_api_key):
        vision = create_mock_vision(req.supplier_name, len(imgs))
    else:
        vision = await extract_remito(
            image_data_uris=imgs, model=req.model, api_key=req.api_key
        )
    return await scan_and_stage_remito(
        db=db,
        vision=vision,
        image_paths=json.dumps(imgs) if imgs else None,
        blanco_bps=req.blanco_pct * 100,
        negro_bps=req.negro_pct * 100,
        iva_rate_bps=req.iva_pct * 100,
    )


@router.patch("/remitos/{id}", response_model=RemitoResponse)
async def patch_remito(
    id: int, req: RemitoHeaderUpdate, db: AsyncSession = Depends(get_async_db)
):
    return await update_remito_header(db=db, remito_id=id, req=req)


@router.post("/remitos/scan-and-stage", response_model=RemitoResponse, status_code=201)
async def scan_and_stage(
    vision: RemitoVisionOutput,
    blanco_pct: int = 60,
    negro_pct: int = 40,
    iva_pct: int = 21,
    db: AsyncSession = Depends(get_async_db),
):
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
    stmt = select(Remito).offset(offset).limit(limit)
    if status:
        stmt = stmt.where(Remito.status == status)
    return (await db.scalars(stmt)).all()


@router.get("/remitos/{id}", response_model=RemitoResponse)
async def get_remito(id: int, db: AsyncSession = Depends(get_async_db)):
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
    return await update_remito_item(db=db, remito_id=id, item_id=item_id, req=req)


@router.post("/remitos/{id}/confirm", response_model=RemitoResponse)
async def confirm(id: int, db: AsyncSession = Depends(get_async_db)):
    return await confirm_remito(db=db, remito_id=id)


@router.post("/remitos/{id}/reject", response_model=RemitoResponse)
async def reject(id: int, db: AsyncSession = Depends(get_async_db)):
    return await reject_remito(db=db, remito_id=id)
