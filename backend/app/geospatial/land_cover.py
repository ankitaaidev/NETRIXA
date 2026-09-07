"""
Land-cover context and administrative-region lookup.

LIMITATION (documented, not hidden): this prototype has no access to a
real land-cover raster (e.g. ESA WorldCover) or official administrative
boundary shapefiles — those require downloads from data portals outside
this environment's allowed network domains. Instead:

- land_cover_context() uses a simple, explainable heuristic: proximity to
  a known industrial facility, membership in a known forest-belt anchor
  region, or a rough agricultural-belt state bounding box.
- reverse_geocode_state() uses the same rough rectangular state bounding
  boxes as the Phase 4 seed data (app.geospatial.regions.STATE_BOUNDS).

Both are clearly labeled as approximations in their return values so the
API layer (Phase 9) can pass that caveat through rather than presenting
them as authoritative.
"""
from math import asin, cos, radians, sin, sqrt

from app.geospatial.regions import FOREST_REGIONS, STATE_BOUNDS

AGRICULTURAL_BELT_STATES = {"Punjab", "Haryana", "Bihar", "Madhya Pradesh", "Uttar Pradesh", "West Bengal"}

FOREST_PROXIMITY_DEG = 0.7  # ~75km at these latitudes, generous for a rough anchor-based heuristic


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def reverse_geocode_state(latitude: float, longitude: float) -> str | None:
    """Rough bounding-box based state lookup. Returns None if the point
    doesn't fall within any known state's bounding box (e.g. ocean, or a
    state not in our reference list)."""
    for state, (lat_min, lat_max, lon_min, lon_max) in STATE_BOUNDS.items():
        if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
            return state
    return None


def land_cover_context(latitude: float, longitude: float, nearest_facility_distance_m: float | None) -> dict:
    """
    Returns {"land_cover": str, "basis": str} — `basis` documents WHY this
    label was chosen, since it's a heuristic rather than a measured value.
    """
    if nearest_facility_distance_m is not None and nearest_facility_distance_m <= 2000:
        return {"land_cover": "Industrial", "basis": "within 2km of a known industrial facility"}

    for state, f_lat, f_lon, _district in FOREST_REGIONS:
        if abs(latitude - f_lat) <= FOREST_PROXIMITY_DEG and abs(longitude - f_lon) <= FOREST_PROXIMITY_DEG:
            return {"land_cover": "Forest", "basis": f"within known forest-belt anchor near {state}"}

    state = reverse_geocode_state(latitude, longitude)
    if state in AGRICULTURAL_BELT_STATES:
        return {"land_cover": "Cropland", "basis": f"within {state}'s agricultural-belt bounding region"}

    return {"land_cover": "Mixed/Unclassified", "basis": "no strong land-cover signal from available heuristics"}


def resolve_land_cover(
    known_land_cover: str | None,
    latitude: float,
    longitude: float,
    nearest_facility_distance_m: float | None,
) -> dict:
    """
    Prefer already-known land cover (e.g. set directly by Phase 4's demo
    seed, or in production by whatever ingestion pipeline attached it)
    over the coarse heuristic above. The heuristic in land_cover_context()
    exists specifically for the case where we DON'T already know the
    answer — e.g. freshly ingested live FIRMS points (Phase 12) that
    haven't been enriched yet. Re-deriving a coarser guess when a better
    answer is already on hand would silently throw away information.
    """
    if known_land_cover:
        return {"land_cover": known_land_cover, "basis": "known from source data"}
    return land_cover_context(latitude, longitude, nearest_facility_distance_m)
