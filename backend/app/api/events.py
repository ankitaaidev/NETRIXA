from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.alert import Alert
from app.models.analyst_feedback import AnalystFeedback
from app.models.enums import FeedbackDecision
from app.models.event_analysis import EventAnalysis
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.schemas.events import FeedbackIn, PaginatedEventsOut, ThermalEventOut
from app.schemas.serializers import serialize_event
from app.services.pipeline import process_event

router = APIRouter()


@router.get("/events", response_model=PaginatedEventsOut)
def list_events(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=2000),
    state: str | None = None,
    district: str | None = None,
    classification: str | None = None,
    riskLevel: str | None = None,
    minConfidence: float | None = Query(None, ge=0, le=100),
    persistence: str | None = None,
    dateFrom: date | None = None,
    dateTo: date | None = None,
    search: str | None = None,
):
    stmt = select(ThermalEvent, EventAnalysis).join(
        EventAnalysis, EventAnalysis.event_id == ThermalEvent.event_id, isouter=True
    )

    if state:
        stmt = stmt.where(ThermalEvent.state == state)
    if district:
        stmt = stmt.where(ThermalEvent.district == district)
    if classification:
        stmt = stmt.where(EventAnalysis.classification == classification)
    if riskLevel:
        stmt = stmt.where(EventAnalysis.risk_level == riskLevel)
    if minConfidence is not None:
        stmt = stmt.where(ThermalEvent.confidence >= minConfidence)
    if persistence:
        stmt = stmt.where(EventAnalysis.persistence == persistence)
    if dateFrom:
        stmt = stmt.where(ThermalEvent.detection_time >= dateFrom)
    if dateTo:
        # Include the complete calendar day selected by the UI.
        stmt = stmt.where(ThermalEvent.detection_time < dateTo + timedelta(days=1))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            (ThermalEvent.event_id.ilike(like))
            | (ThermalEvent.state.ilike(like))
            | (ThermalEvent.district.ilike(like))
            | (EventAnalysis.facility_name.ilike(like))
        )

    all_rows = db.execute(stmt).all()
    total = len(all_rows)

    start = (page - 1) * pageSize
    page_rows = all_rows[start: start + pageSize]

    items = [serialize_event(evt, analysis) for evt, analysis in page_rows]
    return PaginatedEventsOut(items=items, total=total, page=page, pageSize=pageSize)

@router.get("/events/historical-risk-trend")
def historical_risk_trend(db: Session = Depends(get_db)):
    rows = db.execute(
        select(ThermalEvent.detection_time, EventAnalysis.risk_level)
        .join(
            EventAnalysis,
            EventAnalysis.event_id == ThermalEvent.event_id,
            isouter=True,
        )
        .where(EventAnalysis.risk_level.isnot(None))
        .order_by(ThermalEvent.detection_time)
    ).all()

    if not rows:
        return []

    latest_date = max(row[0].date() for row in rows)
    start_date = latest_date - timedelta(days=29)

    daily = {}

    for detection_time, risk_level in rows:
        event_date = detection_time.date()

        if event_date < start_date or event_date > latest_date:
            continue

        if event_date not in daily:
            daily[event_date] = {
                "date": event_date.isoformat(),
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0,
            }

        level = risk_level.value.lower()

        if level in daily[event_date]:
            daily[event_date][level] += 1

    result = []

    for offset in range(30):
        current_date = start_date + timedelta(days=offset)

        if current_date in daily:
            result.append(daily[current_date])
        else:
            result.append({
                "date": current_date.isoformat(),
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0,
            })

    return result
@router.get("/events/{event_id}", response_model=ThermalEventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.get(ThermalEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    analysis = db.execute(
        select(EventAnalysis).where(EventAnalysis.event_id == event_id)
    ).scalar_one_or_none()
    observations = db.execute(
        select(HistoricalObservation).where(HistoricalObservation.event_id == event_id)
    ).scalars().all()
    return serialize_event(event, analysis, observations)


@router.get("/events/{event_id}/history", response_model=list[dict])
def get_event_history(event_id: str, db: Session = Depends(get_db)):
    event = db.get(ThermalEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    observations = db.execute(
        select(HistoricalObservation)
        .where(HistoricalObservation.event_id == event_id)
        .order_by(HistoricalObservation.obs_date)
    ).scalars().all()
    return [
        {"date": o.obs_date.strftime("%Y-%m-%d"), "intensity": o.intensity, "frp": o.frp, "isAnomaly": o.is_anomaly}
        for o in observations
    ]



@router.post("/events/{event_id}/analyze", response_model=ThermalEventOut)
def analyze_event(event_id: str, db: Session = Depends(get_db)):
    """Re-runs the geospatial -> temporal -> classifier -> risk pipeline for
    a single event on demand and returns the refreshed result."""
    event = db.get(ThermalEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    analysis = process_event(db, event)
    db.commit()
    observations = db.execute(
        select(HistoricalObservation).where(HistoricalObservation.event_id == event_id)
    ).scalars().all()
    return serialize_event(event, analysis, observations)


@router.post("/events/{event_id}/feedback")
def submit_feedback(event_id: str, feedback: FeedbackIn, db: Session = Depends(get_db)):
    event = db.get(ThermalEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    try:
        decision = FeedbackDecision(feedback.decision)
    except ValueError:
        valid = [d.value for d in FeedbackDecision]
        raise HTTPException(status_code=422, detail=f"decision must be one of {valid}")

    entry = AnalystFeedback(event_id=event_id, decision=decision, analyst_note=feedback.analystNote)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "eventId": event_id, "decision": decision.value, "createdAt": entry.created_at.isoformat()}
