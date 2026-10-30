from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.modules.closure.models import ClosureStatus, FinancialClosure
from server.modules.closure.scheduler import ARGENTINA_TZ, check_and_apply_schedule


@pytest.mark.anyio
async def test_scheduler_auto_open_at_operating_hours(async_session: AsyncSession):
    # Simulate 10:00 AM in Argentina time
    mock_now = datetime(2026, 10, 30, 10, 0, 0, tzinfo=ARGENTINA_TZ).astimezone(
        timezone.utc
    )

    result = await check_and_apply_schedule(async_session, now_dt=mock_now)
    assert result["action"] == "auto_opened"
    closure_id = result["closure_id"]
    assert closure_id is not None

    closure = await async_session.get(FinancialClosure, closure_id)
    assert closure is not None
    assert closure.status == ClosureStatus.OPEN
    assert closure.initial_cash == 0


@pytest.mark.anyio
async def test_scheduler_auto_close_at_2030(async_session: AsyncSession):
    # Open a session at 15:00
    open_time = datetime(2026, 10, 30, 15, 0, 0, tzinfo=ARGENTINA_TZ).astimezone(
        timezone.utc
    )
    open_res = await check_and_apply_schedule(async_session, now_dt=open_time)
    closure_id = open_res["closure_id"]

    # Now simulate 20:45 PM (after 20:30 closing time)
    close_time = datetime(2026, 10, 30, 20, 45, 0, tzinfo=ARGENTINA_TZ).astimezone(
        timezone.utc
    )
    close_res = await check_and_apply_schedule(async_session, now_dt=close_time)
    assert close_res["action"] == "auto_closed"
    assert close_res["closure_id"] == closure_id

    closure = await async_session.get(FinancialClosure, closure_id)
    assert closure is not None
    assert closure.status == ClosureStatus.CLOSED
    assert closure.auto_closed is True
