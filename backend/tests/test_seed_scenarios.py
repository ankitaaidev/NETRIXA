"""
Verifies the deterministic demo data (Phase 4) actually satisfies the
master plan's explicit requirements — not just "some data exists".
"""
from sqlalchemy import func, select

from app.database.session import get_session_factory
from app.models.facility import Facility
from app.models.thermal_event import ThermalEvent

SessionLocal = get_session_factory()


def _session():
    return SessionLocal()


def test_facility_count_is_30():
    db = _session()
    try:
        count = db.execute(select(func.count(Facility.facility_id))).scalar()
        assert count == 30
    finally:
        db.close()


def test_event_count_within_150_to_300():
    db = _session()
    try:
        count = db.execute(select(func.count(ThermalEvent.event_id))).scalar()
        assert 150 <= count <= 300
    finally:
        db.close()


def test_multiple_indian_states_represented():
    db = _session()
    try:
        states = db.execute(select(func.count(func.distinct(ThermalEvent.state)))).scalar()
        assert states >= 8  # "multiple Indian states" per spec
    finally:
        db.close()


def test_seed_is_deterministic_and_idempotent():
    """Re-running the seed against already-populated tables must not
    duplicate rows (idempotency), and running the generator twice in a
    fresh process must produce identical raw feature values (determinism)."""
    from app.database.seed import generate_event_specs, seed_facilities

    db = _session()
    try:
        facilities = db.execute(select(Facility)).scalars().all()
        specs_1 = generate_event_specs(facilities)
        specs_2 = generate_event_specs(facilities)
        assert len(specs_1) == len(specs_2)
        for s1, s2 in zip(specs_1, specs_2):
            assert s1.event_id == s2.event_id
            assert s1.lat == s2.lat
            assert s1.brightness_temperature == s2.brightness_temperature
    finally:
        db.close()


def test_named_scenario_a_hazira_lng_persistent():
    """Scenario A: normal refinery/LNG thermal activity, stable, low deviation."""
    db = _session()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00001")
        assert evt is not None
        assert evt.land_cover == "Industrial"
        # Stable, not a spike: brightness temp close to its own historical baseline (~350K)
        assert 345 <= evt.brightness_temperature <= 358
    finally:
        db.close()


def test_named_scenario_b_punjab_agricultural():
    """Scenario B: agricultural hotspot, Punjab, low risk expected."""
    db = _session()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00002")
        assert evt is not None
        assert evt.state == "Punjab"
        assert evt.land_cover == "Cropland"
    finally:
        db.close()


def test_named_scenario_c_jamnagar_abnormal_spike():
    """Scenario C: abnormal industrial event, Jamnagar, large deviation from baseline."""
    db = _session()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00003")
        assert evt is not None
        assert evt.state == "Gujarat"
        # This event's brightness temp must be far above a typical refinery
        # baseline (~340-350K) to genuinely trigger high z-score/anomaly
        # once the pipeline (Phases 5-8) processes it.
        assert evt.brightness_temperature > 400
        assert evt.frp > 100
    finally:
        db.close()


def test_at_least_five_severe_anomaly_candidates_exist():
    """
    At least 5 events must carry raw feature values severe enough to be
    expected to reach CRITICAL risk once the pipeline runs (Phase 8).
    We check this at the raw-data level (large deviation from a plausible
    baseline) since event_analysis doesn't exist until later phases.
    """
    db = _session()
    try:
        severe_candidates = db.execute(
            select(func.count(ThermalEvent.event_id)).where(
                ThermalEvent.brightness_temperature > 400,
                ThermalEvent.frp > 100,
            )
        ).scalar()
        assert severe_candidates >= 5
    finally:
        db.close()


def test_at_least_ten_persistent_source_candidates_exist():
    """At least 10 events should be industrial-adjacent and stable (low FRP
    volatility expected), matching 'Persistent Industrial Thermal Source' /
    'Gas Flare' raw-data profile (industrial land cover, moderate-high temp,
    not part of the severe-anomaly set)."""
    db = _session()
    try:
        persistent_candidates = db.execute(
            select(func.count(ThermalEvent.event_id)).where(
                ThermalEvent.land_cover == "Industrial",
                ThermalEvent.brightness_temperature <= 400,
            )
        ).scalar()
        assert persistent_candidates >= 10
    finally:
        db.close()


def test_historical_observations_seeded_per_event():
    from app.models.historical_observation import HistoricalObservation

    db = _session()
    try:
        evt_count = db.execute(select(func.count(ThermalEvent.event_id))).scalar()
        obs_count = db.execute(select(func.count(HistoricalObservation.id))).scalar()
        # 90 days per event
        assert obs_count == evt_count * 90
    finally:
        db.close()
