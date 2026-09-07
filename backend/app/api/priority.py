from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.event_analysis import EventAnalysis
from app.models.thermal_event import ThermalEvent
from app.schemas.events import PaginatedEventsOut
from app.schemas.serializers import serialize_event

router = APIRouter()


@router.get("/priority", response_model=PaginatedEventsOut)
def priority_center(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    riskLevel: str | None = None,
):
    stmt = (
        select(ThermalEvent, EventAnalysis)
        .join(EventAnalysis, EventAnalysis.event_id == ThermalEvent.event_id)
        .order_by(EventAnalysis.risk_score.desc())
    )
    if riskLevel and riskLevel != "ALL":
        stmt = stmt.where(EventAnalysis.risk_level == riskLevel)

    all_rows = db.execute(stmt).all()
    total = len(all_rows)
    start = (page - 1) * pageSize
    page_rows = all_rows[start: start + pageSize]

    items = [serialize_event(evt, analysis) for evt, analysis in page_rows]
    return PaginatedEventsOut(items=items, total=total, page=page, pageSize=pageSize)
