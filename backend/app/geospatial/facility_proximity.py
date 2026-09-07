"""
Facility proximity + industrial context.

FIRMS detections are satellite thermal PIXELS, not building-level
measurements (a MODIS pixel is roughly 1km x 1km; VIIRS is finer but still
not building-precision). Every function here is written to respect that:
we never claim a detection occurred "inside" a named facility — only that
it falls within some distance of one, with an explicit confidence label
for how strong that spatial association is. Phrasing helpers below exist
specifically so calling code (Phase 9's API layer) doesn't have to
re-derive safe language each time.
"""
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import ProximityLevel
from app.models.facility import Facility

# Distance thresholds (meters) for facility-attribution confidence.
# Chosen to be conservative given FIRMS pixel sizes (~375m-1km).
PROXIMITY_HIGH_M = 750
PROXIMITY_MEDIUM_M = 2000
PROXIMITY_LOW_M = 5000


@dataclass
class FacilityMatch:
    facility: Facility
    distance_m: float
    proximity: ProximityLevel


def nearest_facility(db: Session, latitude: float, longitude: float) -> FacilityMatch | None:
    """Returns the closest facility to a point, or None if no facilities
    exist within PROXIMITY_LOW_M (beyond that we consider it unattributed
    rather than force a match to something far away)."""
    point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
    distance_expr = func.ST_DistanceSphere(Facility.geom, func.ST_GeomFromEWKT(point_wkt))

    row = db.execute(
        select(Facility, distance_expr.label("distance_m"))
        .order_by(distance_expr)
        .limit(1)
    ).first()

    if row is None:
        return None

    facility, distance_m = row
    if distance_m > PROXIMITY_LOW_M:
        return None

    return FacilityMatch(facility=facility, distance_m=float(distance_m), proximity=_proximity_for(distance_m))


def nearby_facilities(db: Session, latitude: float, longitude: float, radius_m: float = 5000) -> list[FacilityMatch]:
    """All facilities within radius_m, nearest first."""
    point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
    distance_expr = func.ST_DistanceSphere(Facility.geom, func.ST_GeomFromEWKT(point_wkt))

    rows = db.execute(
        select(Facility, distance_expr.label("distance_m"))
        .where(distance_expr <= radius_m)
        .order_by(distance_expr)
    ).all()

    return [
        FacilityMatch(facility=f, distance_m=float(d), proximity=_proximity_for(d))
        for f, d in rows
    ]


def _proximity_for(distance_m: float) -> ProximityLevel:
    if distance_m <= PROXIMITY_HIGH_M:
        return ProximityLevel.HIGH
    if distance_m <= PROXIMITY_MEDIUM_M:
        return ProximityLevel.MEDIUM
    if distance_m <= PROXIMITY_LOW_M:
        return ProximityLevel.LOW
    return ProximityLevel.NONE


def safe_attribution_phrase(match: FacilityMatch | None) -> str:
    """
    Produces the exact kind of cautious language the master spec requires:
    never "detected inside {facility}", always "anomaly within/near
    {facility}" scaled by confidence.
    """
    if match is None:
        return "No industrial facility identified within 5 km of this detection."
    if match.proximity == ProximityLevel.HIGH:
        return f"Thermal anomaly within the immediate vicinity of {match.facility.name} (~{match.distance_m:.0f} m)."
    if match.proximity == ProximityLevel.MEDIUM:
        return f"Thermal anomaly near {match.facility.name} (~{match.distance_m:.0f} m) — facility association likely but not confirmed."
    return f"Thermal anomaly in the broader area of {match.facility.name} (~{match.distance_m:.0f} m) — facility association is uncertain at this distance."
