from sqlalchemy import select

from app.database.session import get_session_factory
from app.models.enums import PersistenceType
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.services.temporal_service import analyze_history

SessionLocal = get_session_factory()


def _observations_for(event_id):
    db = SessionLocal()
    try:
        return db.execute(
            select(HistoricalObservation).where(HistoricalObservation.event_id == event_id)
        ).scalars().all(), db.get(ThermalEvent, event_id)
    finally:
        db.close()


def test_scenario_a_hazira_is_normal_persistent():
    """Scenario A: stable refinery/LNG activity, should read as NORMAL_PERSISTENT, low z."""
    obs, evt = _observations_for("NTX-IND-00001")
    result = analyze_history(obs, evt.brightness_temperature)
    assert result.persistence == PersistenceType.NORMAL_PERSISTENT
    assert abs(result.z_score) < 1.5
    assert result.observations == 90


def test_scenario_c_jamnagar_is_sudden_event_with_high_zscore():
    """Scenario C: sharp spike far above refinery baseline, should read as
    SUDDEN_EVENT with a large positive z-score."""
    obs, evt = _observations_for("NTX-IND-00003")
    result = analyze_history(obs, evt.brightness_temperature)
    assert result.persistence == PersistenceType.SUDDEN_EVENT
    assert result.z_score > 3.0
    assert result.spatial_change_score > 0.5


def test_empty_history_returns_unknown_gracefully():
    result = analyze_history([], current_value=350.0)
    assert result.persistence == PersistenceType.UNKNOWN
    assert result.observations == 0
    assert result.historical_std == 0.0


def test_persistence_score_and_spatial_change_score_are_bounded():
    obs, evt = _observations_for("NTX-IND-00003")
    result = analyze_history(obs, evt.brightness_temperature)
    assert 0.0 <= result.persistence_score <= 1.0
    assert 0.0 <= result.spatial_change_score <= 1.0


def test_wildfire_event_shows_high_deviation_by_construction():
    """Wildfire events were seeded with is_anomaly_recent=True and a low
    baseline, so any wildfire event should show a clearly elevated z-score."""
    db = SessionLocal()
    try:
        wildfire_evt = db.execute(
            select(ThermalEvent).where(ThermalEvent.event_id.like("NTX-WLD-%")).limit(1)
        ).scalar_one()
    finally:
        db.close()
    obs, evt = _observations_for(wildfire_evt.event_id)
    result = analyze_history(obs, evt.brightness_temperature)
    assert result.z_score > 1.0
