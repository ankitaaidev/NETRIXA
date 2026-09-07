"""
POST /api/reports/events/{event_id}

Returns a structured JSON report payload. We deliberately do NOT claim to
generate a PDF here — the frontend's Reports.tsx page already renders its
own printable report layout entirely from event fields; this endpoint's
job is just to supply real, pipeline-computed data for it to render,
plus a report-level timestamp and disclaimer.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.event_analysis import EventAnalysis
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.schemas.serializers import serialize_event

router = APIRouter()


@router.post("/reports/events/{event_id}")
def generate_report(event_id: str, db: Session = Depends(get_db)):
    event = db.get(ThermalEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    analysis = db.execute(
        select(EventAnalysis).where(EventAnalysis.event_id == event_id)
    ).scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=409, detail=f"Event {event_id} has not been analyzed yet.")

    observations = db.execute(
        select(HistoricalObservation).where(HistoricalObservation.event_id == event_id)
    ).scalars().all()

    return {
        "reportType": "NETRIXA Intelligence Report — Prototype",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "PROTOTYPE — classification and risk scoring are indicative, not production-validated. Intended for human review.",
        "event": serialize_event(event, analysis, observations).model_dump(),
    }
