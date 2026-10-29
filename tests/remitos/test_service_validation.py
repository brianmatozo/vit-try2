import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.exceptions import InvalidMovementError
from server.modules.remitos.models import RemitoStatus
from server.modules.remitos.schemas import (
    ExtractedLineItem,
    RemitoVisionOutput,
)
from server.modules.remitos.service import (
    confirm_remito,
    reject_remito,
    scan_and_stage_remito,
)


@pytest.mark.anyio
async def test_confirm_unlinked_item_raises(async_session: AsyncSession):
    vision = RemitoVisionOutput(
        supplier_name="New Day",
        items=[
            ExtractedLineItem(
                line_index=0,
                raw_description="Unknown Item x 10 u",
                quantity=1,
                unit_cost=5000,
                line_total=5000,
            )
        ],
    )
    staged = await scan_and_stage_remito(async_session, vision)
    assert staged.id is not None
    with pytest.raises(InvalidMovementError, match="not linked to any product"):
        await confirm_remito(async_session, staged.id)


@pytest.mark.anyio
async def test_reject_remito(async_session: AsyncSession):
    vision = RemitoVisionOutput(
        supplier_name="New Day",
        items=[],
    )
    staged = await scan_and_stage_remito(async_session, vision)
    assert staged.id is not None
    rejected = await reject_remito(async_session, staged.id)
    assert rejected.status == RemitoStatus.REJECTED
