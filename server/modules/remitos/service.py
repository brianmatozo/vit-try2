from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from sqlmodel import select

from server.core.exceptions import EntityNotFoundError, InvalidMovementError
from server.modules.catalog.models import Product
from server.modules.inventory.models import InventoryLedger
from server.modules.remitos.fiscal import compute_unit_cost
from server.modules.remitos.matching import (
    match_supplier_item,
    upsert_alias_mapping,
)
from server.modules.remitos.models import (
    MatchStrategy,
    Remito,
    RemitoItem,
    RemitoStatus,
    TargetUnitType,
)
from server.modules.remitos.schemas import (
    RemitoHeaderUpdate,
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
    remito = Remito(
        remito_number=vision.remito_number,
        supplier_name=vision.supplier_name.strip(),
        status=RemitoStatus.STAGED,
        image_paths=image_paths,
        page_count=vision.page_count,
        fiscal_blanco_bps=blanco_bps,
        fiscal_negro_bps=negro_bps,
        iva_rate_bps=iva_rate_bps,
        total_raw_amount=sum(it.line_total for it in vision.items),
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
        cost = compute_unit_cost(
            it.unit_cost,
            mult,
            blanco_bps,
            negro_bps,
            iva_rate_bps,
            is_bulk=target_t == TargetUnitType.BULK_GRAMS,
        )
        total_real += it.quantity * cost.real_pack_cost

        db.add(
            RemitoItem(
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
                quantity_to_commit=it.quantity * mult,
                calculated_unit_cost=cost.real_unit_cost,
                match_confidence=conf,
                match_strategy=strat,
            )
        )

    remito.total_real_amount = total_real
    await db.commit()
    await db.refresh(remito)
    return remito


async def _get_staged_remito(db: AsyncSession, remito_id: int) -> Remito:
    """Fetch locked remito and assert it is in STAGED status."""
    stmt = select(Remito).where(Remito.id == remito_id).with_for_update()
    remito = (await db.scalars(stmt)).first()
    if not remito:
        raise EntityNotFoundError("Remito", remito_id)
    if remito.status != RemitoStatus.STAGED:
        raise InvalidMovementError(f"Remito is {remito.status}, expected staged")
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

    remito = await _get_staged_remito(db, remito_id)

    if req.product_id is not None:
        item.product_id = req.product_id
        item.match_strategy = MatchStrategy.MANUAL_OVERRIDE
        item.match_confidence = 100
        item.is_verified_by_user = True

    fields = (
        "multiplier",
        "package_type",
        "target_unit_type",
        "effective_quantity",
        "is_verified_by_user",
    )
    for a in fields:
        if (v := getattr(req, a, None)) is not None:
            setattr(item, a, v)

    item.quantity_to_commit = item.effective_quantity * item.multiplier
    cost = compute_unit_cost(
        item.extracted_unit_cost,
        item.multiplier,
        remito.fiscal_blanco_bps,
        remito.fiscal_negro_bps,
        remito.iva_rate_bps,
        is_bulk=item.target_unit_type == TargetUnitType.BULK_GRAMS,
    )
    item.calculated_unit_cost = cost.real_unit_cost
    await db.commit()
    await db.refresh(item)
    return item


async def update_remito_header(
    db: AsyncSession, remito_id: int, req: RemitoHeaderUpdate
) -> Remito:
    """Update remito header (fiscal split or notes) and recalculate item costs."""
    remito = await _get_staged_remito(db, remito_id)

    if req.fiscal_blanco_pct is not None:
        remito.fiscal_blanco_bps = req.fiscal_blanco_pct * 100
    if req.fiscal_negro_pct is not None:
        remito.fiscal_negro_bps = req.fiscal_negro_pct * 100
    if req.iva_pct is not None:
        remito.iva_rate_bps = req.iva_pct * 100
    if req.notes is not None:
        remito.notes = req.notes

    stmt = select(RemitoItem).where(RemitoItem.remito_id == remito_id)
    items = (await db.scalars(stmt)).all()
    total_real = 0
    for it in items:
        cost = compute_unit_cost(
            it.extracted_unit_cost,
            it.multiplier,
            remito.fiscal_blanco_bps,
            remito.fiscal_negro_bps,
            remito.iva_rate_bps,
            is_bulk=it.target_unit_type == TargetUnitType.BULK_GRAMS,
        )
        it.calculated_unit_cost = cost.real_unit_cost
        total_real += it.effective_quantity * cost.real_pack_cost

    remito.total_real_amount = total_real
    await db.commit()
    await db.refresh(remito)
    return remito


async def confirm_remito(db: AsyncSession, remito_id: int) -> Remito:
    """Atomic double-entry stock commitment and alias dictionary caching."""
    remito = await _get_staged_remito(db, remito_id)
    items = (
        await db.scalars(select(RemitoItem).where(RemitoItem.remito_id == remito_id))
    ).all()

    for it in items:
        if it.quantity_to_commit > 0 and not it.product_id:
            raise InvalidMovementError(
                f"Item '{it.raw_description}' is not linked to any product"
            )

    for it in items:
        if it.quantity_to_commit <= 0 or not it.product_id:
            continue

        prod_q = select(Product).options(noload("*")).where(Product.id == it.product_id)
        prod = (await db.scalars(prod_q.with_for_update())).one()
        assert prod.id is not None
        prod_id: int = prod.id
        prod.current_stock += it.quantity_to_commit
        prod.last_cost = it.calculated_unit_cost

        remito_ref = remito.remito_number or remito.id
        db.add(
            InventoryLedger(
                product_id=prod_id,
                movement_type="receiving",
                quantity_delta=it.quantity_to_commit,
                balance_after=prod.current_stock,
                reference_id=f"REMITO-{remito.id}",
                notes=f"Remito {remito_ref}: {it.raw_description[:40]}",
            )
        )

        await upsert_alias_mapping(
            db=db,
            supplier_name=remito.supplier_name,
            raw_description=it.raw_description,
            product_id=prod_id,
            multiplier=it.multiplier,
            package_type=it.package_type,
            target_unit_type=it.target_unit_type,
        )

    remito.status = RemitoStatus.COMMITTED
    remito.committed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(remito)
    return remito


async def reject_remito(db: AsyncSession, remito_id: int) -> Remito:
    """Discard a staged remito."""
    remito = await _get_staged_remito(db, remito_id)
    remito.status = RemitoStatus.REJECTED
    await db.commit()
    await db.refresh(remito)
    return remito
