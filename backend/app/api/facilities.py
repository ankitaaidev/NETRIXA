from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time_utils import reference_now
from app.database.session import get_db
from app.models.enums import RiskLevel
from app.models.event_analysis import EventAnalysis
from app.models.facility import Facility
from app.models.thermal_event import ThermalEvent
from app.schemas.events import FacilityOut

router = APIRouter()

NEARBY_RADIUS_M = 5000


def _facility_stats(db: Session, facility: Facility) -> FacilityOut:
    point_wkt = f"SRID=4326;POINT({facility.longitude} {facility.latitude})"
    distance_expr = func.ST_DistanceSphere(ThermalEvent.geom, func.ST_GeomFromEWKT(point_wkt))

    now = reference_now()
    cutoff_30 = now - timedelta(days=30)
    cutoff_90 = now - timedelta(days=90)

    nearby_90d = db.execute(
        select(ThermalEvent, EventAnalysis)
        .join(EventAnalysis, EventAnalysis.event_id == ThermalEvent.event_id, isouter=True)
        .where(distance_expr <= NEARBY_RADIUS_M, ThermalEvent.detection_time >= cutoff_90)
    ).all()

    activity_30d = sum(1 for evt, _ in nearby_90d if evt.detection_time >= cutoff_30)
    activity_90d = len(nearby_90d)
    flagged = [
        (evt, analysis) for evt, analysis in nearby_90d
        if analysis and analysis.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    ]
    nearby_flagged_count = len(flagged)

    if any(a.risk_level == RiskLevel.CRITICAL for _, a in nearby_90d if a):
        status = "CRITICAL"
    elif any(a.risk_level == RiskLevel.HIGH for _, a in nearby_90d if a):
        status = "ABNORMAL"
    elif activity_30d > 0 and activity_90d > 0 and (activity_30d / max(activity_90d, 1)) > 0.5:
        status = "WATCH"
    else:
        status = "NORMAL"

    last_activity = max((evt.detection_time for evt, _ in nearby_90d), default=None)

    return FacilityOut(
        id=facility.facility_id,
        facilityId=facility.facility_id,
        name=facility.name,
        facilityType=facility.facility_type,
        latitude=facility.latitude,
        longitude=facility.longitude,
        state=facility.state,
        district=facility.district,
        status=status,
        thermalActivity30d=activity_30d,
        thermalActivity90d=activity_90d,
        nearbyEvents=nearby_flagged_count,
        lastActivity=last_activity.strftime("%Y-%m-%d") if last_activity else None,
    )


@router.get("/facilities", response_model=list[FacilityOut])
def list_facilities(db: Session = Depends(get_db)):
    facilities = db.execute(select(Facility)).scalars().all()
    return [_facility_stats(db, f) for f in facilities]


@router.get("/facilities/{facility_id}", response_model=FacilityOut)
def get_facility(facility_id: str, db: Session = Depends(get_db)):
    facility = db.get(Facility, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility {facility_id} not found.")
    return _facility_stats(db, facility)
