from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.geospatial.geojson_utils import feature_collection, point_feature
from app.models.event_analysis import EventAnalysis
from app.models.facility import Facility
from app.models.thermal_event import ThermalEvent

router = APIRouter()


@router.get("/map/events")
def map_events(db: Session = Depends(get_db)):
    rows = db.execute(
        select(ThermalEvent, EventAnalysis).join(
            EventAnalysis, EventAnalysis.event_id == ThermalEvent.event_id, isouter=True
        )
    ).all()

    features = []
    for evt, analysis in rows:
        features.append(point_feature(evt.longitude, evt.latitude, {
            "id": evt.event_id,
            "eventId": evt.event_id,
            "classification": analysis.classification.value if analysis else "Unknown / Insufficient Evidence",
            "riskLevel": analysis.risk_level.value if analysis else "LOW",
            "riskScore": analysis.risk_score if analysis else 0,
            "state": evt.state,
            "district": evt.district,
        }))
    return feature_collection(features)


@router.get("/map/facilities")
def map_facilities(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    db: Session = Depends(get_db),
):
    envelope = func.ST_MakeEnvelope(
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        4326,
    )

    facilities = db.execute(
        select(Facility).where(
            func.ST_Intersects(Facility.geom, envelope)
        )
    ).scalars().all()

    features = [
        point_feature(f.longitude, f.latitude, {
            "id": f.facility_id,
            "facilityId": f.facility_id,
            "name": f.name,
            "facilityType": f.facility_type,
            "state": f.state,
            "district": f.district,
        })
        for f in facilities
    ]

    return feature_collection(features)