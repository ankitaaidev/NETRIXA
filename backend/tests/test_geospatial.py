from app.database.session import get_session_factory
from app.geospatial.facility_proximity import (
    nearby_facilities,
    nearest_facility,
    safe_attribution_phrase,
)
from app.geospatial.land_cover import land_cover_context, reverse_geocode_state
from app.models.enums import ProximityLevel
from app.models.thermal_event import ThermalEvent

SessionLocal = get_session_factory()


def _session():
    return SessionLocal()


def test_nearest_facility_finds_jamnagar_for_scenario_c():
    """Scenario C's event is seeded ~0.01 deg from Jamnagar Refinery — must
    resolve back to it with HIGH proximity confidence."""
    db = _session()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00003")
        match = nearest_facility(db, evt.latitude, evt.longitude)
        assert match is not None
        assert match.facility.facility_id == "FAC-001"
        assert match.proximity == ProximityLevel.HIGH
        assert match.distance_m < 750
    finally:
        db.close()


def test_nearest_facility_returns_none_far_from_everything():
    db = _session()
    try:
        # Middle of the Bay of Bengal — nowhere near any seeded facility.
        match = nearest_facility(db, 15.0, 88.0)
        assert match is None
    finally:
        db.close()


def test_nearby_facilities_ordered_by_distance():
    db = _session()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00001")  # near Hazira LNG
        matches = nearby_facilities(db, evt.latitude, evt.longitude, radius_m=50000)
        assert len(matches) >= 1
        distances = [m.distance_m for m in matches]
        assert distances == sorted(distances)
    finally:
        db.close()


def test_safe_attribution_phrase_never_claims_inside():
    db = _session()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00003")
        match = nearest_facility(db, evt.latitude, evt.longitude)
        phrase = safe_attribution_phrase(match)
        assert "inside" not in phrase.lower()
        assert "within" in phrase.lower() or "near" in phrase.lower()
    finally:
        db.close()


def test_safe_attribution_phrase_handles_no_match():
    phrase = safe_attribution_phrase(None)
    assert "no industrial facility identified" in phrase.lower()


def test_land_cover_context_industrial_near_facility():
    result = land_cover_context(22.3675, 69.8747, nearest_facility_distance_m=100)
    assert result["land_cover"] == "Industrial"
    assert "basis" in result


def test_land_cover_context_cropland_in_punjab():
    result = land_cover_context(31.0, 75.0, nearest_facility_distance_m=None)
    assert result["land_cover"] == "Cropland"


def test_reverse_geocode_state_matches_known_point():
    state = reverse_geocode_state(22.3675, 69.8747)  # Jamnagar
    assert state == "Gujarat"


def test_reverse_geocode_state_returns_none_outside_known_bounds():
    state = reverse_geocode_state(0.0, 0.0)  # Gulf of Guinea
    assert state is None
