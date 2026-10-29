from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from server.modules.remitos.fiscal import compute_unit_cost
from server.modules.remitos.matching import match_supplier_item
from server.modules.remitos.models import (
    Remito,
    RemitoItem,
    RemitoStatus,
    TargetUnitType,
)
from server.modules.remitos.schemas import ExtractedLineItem, RemitoVisionOutput


def create_mock_vision(supplier: str | None, count: int) -> RemitoVisionOutput:
    """Generate default mock vision output for offline testing and demos."""
    ts = datetime.now().strftime("%m%d-%H%M")
    return RemitoVisionOutput(
        supplier_name=supplier or "Distribuidora New Day",
        remito_number=f"R-{ts}",
        page_count=count or 1,
        items=[
            ExtractedLineItem(
                line_index=0,
                raw_description="Barritas Almendra x 41 gr x 10 u",
                quantity=2,
                unit_cost=5000,
                line_total=10000,
            ),
            ExtractedLineItem(
                line_index=1,
                raw_description="Yerba Kalena x 2 kg x 5 u",
                quantity=3,
                unit_cost=12000,
                line_total=36000,
            ),
        ],
        overall_confidence=92,
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
        overall_confidence=vision.overall_confidence,
        fiscal_blanco_bps=blanco_bps,
        fiscal_negro_bps=negro_bps,
        iva_rate_bps=iva_rate_bps,
        total_raw_amount=sum(it.line_total for it in vision.items),
    )
    db.add(remito)
    await db.flush()
    remito_id = remito.id
    assert remito_id is not None

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
