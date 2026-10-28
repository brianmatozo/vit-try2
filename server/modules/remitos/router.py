from fastapi import APIRouter, Depends, Query
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from server.core.dependencies import get_async_db
from server.core.exceptions import EntityNotFoundError
from server.modules.remitos.models import (
    Remito,
    RemitoStatus,
    SupplierProductMapping,
)
from server.modules.remitos.schemas import (
    RemitoItemResponse,
    RemitoItemUpdate,
    RemitoResponse,
    RemitoVisionOutput,
    SupplierMappingResponse,
)
from server.modules.remitos.service import (
    confirm_remito,
    reject_remito,
    scan_and_stage_remito,
    update_remito_item,
)

router = APIRouter(tags=["remitos"])


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
