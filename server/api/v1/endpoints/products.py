"""API endpoints for products: FastCRUD operations and barcode scanning."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastcrud import crud_router
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlmodel import select

from server.core.dependencies import get_async_db
from server.models.products import Product
from server.schemas.products import (
    ProductCreate,
    ProductResponse,
    ProductScanResult,
    ProductUpdate,
)
from server.utils.barcode import parse_barcode

# Custom domain router for scanner and PLU lookups
custom_router = APIRouter(prefix="/products", tags=["Products"])


@custom_router.get(
    "/scan/{barcode}",
    response_model=ProductScanResult,
    summary="Scan barcode (discrete or scale weight embedded)",
    description="Parses SKU or EAN-13 scale embedded barcode and computes subtotal.",
    operation_id="scanBarcode",
)
async def scan_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_async_db),
) -> ProductScanResult:
    parsed = parse_barcode(barcode)
    if (
        parsed.is_embedded_scale
        or parsed.is_embedded_price
        or parsed.is_embedded_weight
    ):
        stmt = (
            select(Product)
            .options(noload("*"))
            .where(Product.plu_code == parsed.sku_or_plu)
        )
        product = (await db.scalars(stmt)).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bulk product with PLU code '{parsed.sku_or_plu}' not found",
            )
        ref_grams = (
            product.bulk_reference_grams if product.bulk_reference_grams > 0 else 100
        )
        if parsed.is_embedded_price and parsed.embedded_price_whole_ars is not None:
            line_total = parsed.embedded_price_whole_ars
            weight = (
                round((line_total / product.unit_price) * ref_grams)
                if product.unit_price > 0
                else 0
            )
        else:
            weight = parsed.weight_grams or 0
            line_total = round((product.unit_price / ref_grams) * weight)

        return ProductScanResult(
            raw_barcode=parsed.raw_barcode,
            is_embedded_weight=True,
            weight_grams=weight,
            product=ProductResponse.model_validate(product),
            line_total=line_total,
        )

    stmt = select(Product).options(noload("*")).where(Product.sku == parsed.sku_or_plu)
    product = (await db.scalars(stmt)).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discrete product with SKU '{parsed.sku_or_plu}' not found",
        )
    return ProductScanResult(
        raw_barcode=parsed.raw_barcode,
        is_embedded_weight=False,
        weight_grams=None,
        product=ProductResponse.model_validate(product),
        line_total=product.unit_price,
    )


@custom_router.get(
    "/by-plu/{plu_code}",
    response_model=ProductResponse,
    summary="Lookup product by 4-digit PLU",
    description="Lookup scale bulk product by PLU code for touch screen grid or POS.",
    operation_id="getProductByPLU",
)
async def get_product_by_plu(
    plu_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ProductResponse:
    stmt = select(Product).options(noload("*")).where(Product.plu_code == plu_code)
    product = (await db.scalars(stmt)).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with PLU '{plu_code}' not found",
        )
    return ProductResponse.model_validate(product)


# FastCRUD generated standard CRUD router
_crud_router = crud_router(
    session=get_async_db,
    model=Product,
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
    select_schema=ProductResponse,
    path="/products",
    tags=["Products"],
)

router = APIRouter()
router.include_router(custom_router)
router.include_router(_crud_router)
