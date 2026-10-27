"""Stock drift audit and paginated ledger queries."""

from collections.abc import Sequence

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from server.modules.inventory.models import InventoryLedger, InventoryMovementType
from server.modules.inventory.movements import get_locked_product
from server.modules.inventory.schemas import StockAuditResponse


async def audit_product_stock(db: AsyncSession, product_id: int) -> StockAuditResponse:
    """Automated stock calculation view comparing stock against ledger history."""
    product = await get_locked_product(db, product_id)

    sum_stmt = select(func.coalesce(func.sum(InventoryLedger.quantity_delta), 0)).where(
        InventoryLedger.product_id == product_id
    )
    ledger_balance = (await db.scalars(sum_stmt)).first() or 0

    virtual_stock = max(
        0, product.current_stock - product.reserved_stock - product.min_safety_buffer
    )
    drift = product.current_stock - ledger_balance

    return StockAuditResponse(
        product_id=product_id,
        sku=product.sku,
        name=product.name,
        product_type=product.product_type,
        current_stock=product.current_stock,
        reserved_stock=product.reserved_stock,
        min_safety_buffer=product.min_safety_buffer,
        virtual_stock=virtual_stock,
        ledger_calculated_balance=ledger_balance,
        drift=drift,
        is_reconciled=(drift == 0),
    )


async def get_ledger_history(
    db: AsyncSession,
    product_id: int | None = None,
    movement_type: InventoryMovementType | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[InventoryLedger]:
    """Query paginated append-only inventory ledger history."""
    stmt = select(InventoryLedger)
    if product_id is not None:
        stmt = stmt.where(InventoryLedger.product_id == product_id)
    if movement_type is not None:
        stmt = stmt.where(InventoryLedger.movement_type == movement_type)

    stmt = stmt.order_by(col(InventoryLedger.id).desc()).limit(limit).offset(offset)
    result = await db.scalars(stmt)
    return result.all()
