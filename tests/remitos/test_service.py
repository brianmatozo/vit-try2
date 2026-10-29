import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.modules.catalog.models import Product, ProductType
from server.modules.inventory.models import InventoryLedger
from server.modules.remitos.models import (
    RemitoStatus,
    SupplierProductMapping,
)
from server.modules.remitos.schemas import (
    ExtractedLineItem,
    RemitoItemUpdate,
    RemitoVisionOutput,
)
from server.modules.remitos.service import (
    confirm_remito,
    scan_and_stage_remito,
    update_remito_item,
)


@pytest.mark.anyio
async def test_stage_update_and_confirm_remito(async_session: AsyncSession):
    # 1. Create product in catalog
    prod = Product(
        sku="BAR-LADDU-1",
        name="Barrita Laddu Chocolate",
        unit_price=2000,
        current_stock=10,
        product_type=ProductType.DISCRETE,
    )
    async_session.add(prod)
    await async_session.commit()

    # 2. Scan and Stage Remito
    vision = RemitoVisionOutput(
        supplier_name="New Day",
        remito_number="0001-1234",
        items=[
            ExtractedLineItem(
                line_index=0,
                raw_description="Barritas Laddu x 12 u",
                quantity=2,
                unit_cost=10000,
                line_total=20000,
            )
        ],
    )
    staged = await scan_and_stage_remito(async_session, vision)
    assert staged.status == RemitoStatus.STAGED
    assert staged.id is not None
    remito_id: int = staged.id
    item_id = staged.items[0].id
    assert item_id is not None

    # 3. Inline update: link to product
    updated_item = await update_remito_item(
        async_session,
        remito_id=remito_id,
        item_id=item_id,
        req=RemitoItemUpdate(product_id=prod.id, effective_quantity=2),
    )
    assert updated_item.product_id == prod.id
    assert updated_item.quantity_to_commit == 24
    assert updated_item.is_verified_by_user is True

    # 4. Confirm Remito
    confirmed = await confirm_remito(
        async_session,
        remito_id,
    )
    assert confirmed.status == RemitoStatus.COMMITTED

    # Verify Product stock increment & last_cost update
    await async_session.refresh(prod)
    assert prod.current_stock == 34  # 10 + 24
    assert prod.last_cost == updated_item.calculated_unit_cost

    # Verify double-entry ledger entry
    ledger = (
        await async_session.scalars(
            select(InventoryLedger).where(InventoryLedger.product_id == prod.id)
        )
    ).first()
    assert ledger is not None
    assert ledger.movement_type == "receiving"
    assert ledger.quantity_delta == 24
    assert ledger.balance_after == 34

    # Verify Alias Dictionary auto-memorized the mapping!
    mapping = (
        await async_session.scalars(
            select(SupplierProductMapping).where(
                SupplierProductMapping.supplier_name == "New Day"
            )
        )
    ).first()
    assert mapping is not None
    assert mapping.product_id == prod.id
    assert mapping.multiplier == 12
