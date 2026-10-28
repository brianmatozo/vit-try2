from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlmodel import col, select

from server.core.exceptions import EntityNotFoundError, InvalidMovementError
from server.modules.catalog.models import Product
from server.modules.inventory.models import InventoryLedger
from server.modules.remitos.fiscal import compute_unit_cost
from server.modules.remitos.matching import (
    match_supplier_item,
    normalize_supplier_text,
)
from server.modules.remitos.models import (
    MatchStrategy,
    Remito,
    RemitoItem,
    RemitoStatus,
    SupplierProductMapping,
    TargetUnitType,
)
from server.modules.remitos.schemas import (
    RemitoItemUpdate,
    RemitoVisionOutput,
)


async def scan_and_stage_remito(
    db: AsyncSession,
    vision: RemitoVisionOutput,
    image_paths: str | None = None,
    blanco_bps: int = 6000,
    negro_bps: int = 4000,
    iva_rate_bps: int = 2100,
) -> Remito:
    """Create a staged remito header and line items with initial matching."""
    total_raw = sum(it.line_total for it in vision.items)
    remito = Remito(
        remito_number=vision.remito_number,
        supplier_name=vision.supplier_name.strip(),
        status=RemitoStatus.STAGED,
        image_paths=image_paths,
        page_count=vision.page_count,
        fiscal_blanco_bps=blanco_bps,
        fiscal_negro_bps=negro_bps,
        iva_rate_bps=iva_rate_bps,
        total_raw_amount=total_raw,
    )
    db.add(remito)
    await db.flush()
    assert remito.id is not None
    remito_id: int = remito.id

    total_real = 0
    for it in vision.items:
        pid, conf, strat, mult, pkg_t, target_t = await match_supplier_item(
            db, vision.supplier_name, it.raw_description
        )
        is_bulk = target_t == TargetUnitType.BULK_GRAMS
        cost = compute_unit_cost(
            pack_price=it.unit_cost,
            multiplier=mult,
            blanco_bps=blanco_bps,
            negro_bps=negro_bps,
            iva_rate_bps=iva_rate_bps,
            is_bulk=is_bulk,
        )
        commit_qty = it.quantity * mult
        total_real += it.quantity * cost.real_pack_cost

        item = RemitoItem(
            remito_id=remito_id,
            line_index=it.line_index,
            raw_description=it.raw_description,
            extracted_quantity=it.quantity,
            extracted_unit_cost=it.unit_cost,
            extracted_line_total=it.line_total,
            product_id=pid,
            package_type=pkg_t,
            multiplier=mult,
            target_unit_type=target_t,
            effective_quantity=it.quantity,
            quantity_to_commit=commit_qty,
            calculated_unit_cost=cost.real_unit_cost,
            match_confidence=conf,
            match_strategy=strat,
        )
        db.add(item)

    remito.total_real_amount = total_real
    await db.commit()
    await db.refresh(remito)
    return remito


async def update_remito_item(
    db: AsyncSession, remito_id: int, item_id: int, req: RemitoItemUpdate
) -> RemitoItem:
    """Inline update a staged remito line item."""
    stmt = select(RemitoItem).where(
        RemitoItem.id == item_id, RemitoItem.remito_id == remito_id
    )
    item = (await db.scalars(stmt)).first()
    if not item:
        raise EntityNotFoundError("RemitoItem", item_id)

    remito = await db.get(Remito, remito_id)
    if not remito or remito.status != RemitoStatus.STAGED:
        raise InvalidMovementError("Cannot edit non-staged remito")

    if req.product_id is not None:
        item.product_id = req.product_id
        item.match_strategy = MatchStrategy.MANUAL_OVERRIDE
        item.match_confidence = 100
        item.is_verified_by_user = True

    if req.multiplier is not None:
        item.multiplier = req.multiplier
    if req.package_type is not None:
        item.package_type = req.package_type
    if req.target_unit_type is not None:
        item.target_unit_type = req.target_unit_type
    if req.effective_quantity is not None:
        item.effective_quantity = req.effective_quantity
    if req.is_verified_by_user is not None:
        item.is_verified_by_user = req.is_verified_by_user

    item.quantity_to_commit = item.effective_quantity * item.multiplier
    is_bulk = item.target_unit_type == TargetUnitType.BULK_GRAMS
    cost = compute_unit_cost(
        pack_price=item.extracted_unit_cost,
        multiplier=item.multiplier,
        blanco_bps=remito.fiscal_blanco_bps,
        negro_bps=remito.fiscal_negro_bps,
        iva_rate_bps=remito.iva_rate_bps,
        is_bulk=is_bulk,
    )
    item.calculated_unit_cost = cost.real_unit_cost
    await db.commit()
    await db.refresh(item)
    return item


async def confirm_remito(db: AsyncSession, remito_id: int) -> Remito:
    """Atomic double-entry stock commitment and alias dictionary caching."""
    remito_stmt = select(Remito).where(Remito.id == remito_id).with_for_update()
    remito = (await db.scalars(remito_stmt)).first()
    if not remito:
        raise EntityNotFoundError("Remito", remito_id)
    if remito.status != RemitoStatus.STAGED:
        raise InvalidMovementError(f"Remito is already {remito.status}")

    items_stmt = select(RemitoItem).where(RemitoItem.remito_id == remito_id)
    items = (await db.scalars(items_stmt)).all()

    for it in items:
        if it.quantity_to_commit > 0 and not it.product_id:
            raise InvalidMovementError(
                f"Item '{it.raw_description}' is not linked to any product"
            )

    for it in items:
        if it.quantity_to_commit <= 0 or not it.product_id:
            continue

        prod_stmt = (
            select(Product)
            .options(noload("*"))
            .where(Product.id == it.product_id)
            .with_for_update()
        )
        prod = (await db.scalars(prod_stmt)).one()
        assert prod.id is not None
        prod_id: int = prod.id
        prod.current_stock += it.quantity_to_commit
        prod.last_cost = it.calculated_unit_cost

        desc_snippet = it.raw_description[:50]
        ledger = InventoryLedger(
            product_id=prod_id,
            movement_type="receiving",
            quantity_delta=it.quantity_to_commit,
            balance_after=prod.current_stock,
            reference_id=f"REMITO-{remito.id}",
            notes=f"Remito {remito.remito_number or remito.id}: {desc_snippet}",
        )
        db.add(ledger)

        # Upsert alias dictionary mapping
        norm_text = normalize_supplier_text(it.raw_description)
        m_stmt = select(SupplierProductMapping).where(
            col(SupplierProductMapping.supplier_name).ilike(remito.supplier_name),
            SupplierProductMapping.raw_item_pattern == norm_text,
        )
        existing = (await db.scalars(m_stmt)).first()
        if existing:
            existing.product_id = prod_id
            existing.multiplier = it.multiplier
            existing.package_type = it.package_type
            existing.target_unit_type = it.target_unit_type
            existing.times_used += 1
            existing.last_matched_at = datetime.now(timezone.utc)
        else:
            new_m = SupplierProductMapping(
                supplier_name=remito.supplier_name,
                raw_item_pattern=norm_text,
                product_id=prod_id,
                package_type=it.package_type,
                multiplier=it.multiplier,
                target_unit_type=it.target_unit_type,
            )
            db.add(new_m)

    remito.status = RemitoStatus.COMMITTED
    remito.committed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(remito)
    return remito


async def reject_remito(db: AsyncSession, remito_id: int) -> Remito:
    """Discard a staged remito."""
    stmt = select(Remito).where(Remito.id == remito_id).with_for_update()
    remito = (await db.scalars(stmt)).first()
    if not remito:
        raise EntityNotFoundError("Remito", remito_id)
    if remito.status != RemitoStatus.STAGED:
        raise InvalidMovementError(f"Cannot reject remito in state {remito.status}")

    remito.status = RemitoStatus.REJECTED
    await db.commit()
    await db.refresh(remito)
    return remito
