from fastapi import APIRouter, Depends, Query
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from server.core.dependencies import get_async_db
from server.core.exceptions import EntityNotFoundError
from server.modules.remitos.models import SupplierProductMapping
from server.modules.remitos.schemas import SupplierMappingResponse

router = APIRouter(tags=["remitos"])


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
