"""Scheduled automation for store operating hours (09:00 open / 20:30 auto-close)."""

from datetime import datetime, time, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from server.modules.closure.engine import auto_close_session, open_closure
from server.modules.closure.models import ClosureStatus, FinancialClosure
from server.modules.closure.queries import get_active_closure
from server.modules.closure.schemas import OpenClosureRequest

# Argentina Standard Time (ART) is UTC-3 year-round
ARGENTINA_TZ = timezone(timedelta(hours=-3))
OPEN_TIME = time(9, 0)
CLOSE_TIME = time(20, 30)


async def check_and_apply_schedule(
    db: AsyncSession, now_dt: datetime | None = None
) -> dict[str, str | int | None]:
    """Evaluates current local store time and applies opening or auto-closing."""
    utc_now = now_dt or datetime.now(timezone.utc)
    local_now = utc_now.astimezone(ARGENTINA_TZ)
    current_time = local_now.time()

    # 1. Past closing time (>= 20:30): auto-close any still-open session
    if current_time >= CLOSE_TIME or current_time < OPEN_TIME:
        active = await get_active_closure(db)
        if active and active.id is not None:
            closed = await auto_close_session(db, active.id)
            return {"action": "auto_closed", "closure_id": closed.id}
        return {"action": "none", "reason": "outside_hours_closed"}

    # 2. Operating hours (09:00 <= time < 20:30): ensure session is open for today
    active = await get_active_closure(db)
    if active:
        return {"action": "none", "reason": "already_open", "closure_id": active.id}

    # Check if a session was already opened and manually closed today
    start_of_day_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_utc = start_of_day_local.astimezone(timezone.utc)

    today_stmt = (
        select(FinancialClosure)
        .where(FinancialClosure.opened_at >= start_of_day_utc)
        .order_by(col(FinancialClosure.id).desc())
    )
    today_closure = (await db.scalars(today_stmt)).first()

    # If already closed today manually, do not re-open automatically
    if today_closure and today_closure.status == ClosureStatus.CLOSED:
        return {
            "action": "none",
            "reason": "already_closed_today",
            "closure_id": today_closure.id,
        }

    # Auto-open morning session
    new_closure = await open_closure(
        db,
        OpenClosureRequest(
            initial_cash=0,
            notes="Apertura automática programada (09:00 hs)",
        ),
    )
    return {"action": "auto_opened", "closure_id": new_closure.id}
