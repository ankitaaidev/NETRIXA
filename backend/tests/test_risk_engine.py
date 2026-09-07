from sqlalchemy import select

from app.database.session import get_session_factory
from app.geospatial.facility_proximity import nearest_facility
from app.geospatial.land_cover import resolve_land_cover
from app.ml.classifier import ClassifierFeatures, ThermalClassifier
from app.models.enums import ProximityLevel, RiskLevel
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.risk.risk_engine import compute_risk
from app.services.temporal_service import analyze_history

SessionLocal = get_session_factory()
classifier = ThermalClassifier()


def _full_pipeline(db, event_id):
    evt = db.get(ThermalEvent, event_id)
    match = nearest_facility(db, evt.latitude, evt.longitude)
    lc = resolve_land_cover(evt.land_cover, evt.latitude, evt.longitude, match.distance_m if match else None)
    obs = db.execute(
        select(HistoricalObservation).where(HistoricalObservation.event_id == event_id)
    ).scalars().all()
    temporal = analyze_history(obs, evt.brightness_temperature)
    features = ClassifierFeatures(
        brightness_temperature=evt.brightness_temperature, frp=evt.frp, confidence=evt.confidence,
        facility_distance_m=match.distance_m if match else None,
        facility_proximity=match.proximity if match else ProximityLevel.NONE,
        land_cover=lc["land_cover"], historical_mean=temporal.historical_mean,
        historical_std=temporal.historical_std, z_score=temporal.z_score,
        persistence=temporal.persistence, recurrence_rate=temporal.recurrence_rate,
        observations=temporal.observations,
    )
    classification_result = classifier.predict(features)
    risk_result = compute_risk(
        z_score=temporal.z_score,
        proximity=match.proximity if match else ProximityLevel.NONE,
        persistence_score=temporal.persistence_score,
        spatial_change_score=temporal.spatial_change_score,
        classification=classification_result.classification,
        classification_confidence=classification_result.confidence,
    )
    return classification_result, risk_result


def test_scenario_a_is_low_risk_observe():
    """Master plan: Scenario A -> Persistent Industrial Thermal Source, Risk: Low, Action: Observe."""
    db = SessionLocal()
    try:
        cls_result, risk_result = _full_pipeline(db, "NTX-IND-00001")
        assert risk_result.risk_level == RiskLevel.LOW
        assert risk_result.risk_score <= 25
    finally:
        db.close()


def test_scenario_b_is_low_risk_no_immediate_action():
    """Master plan: Scenario B -> Agricultural Burning, Risk: Low, Action: No immediate action."""
    db = SessionLocal()
    try:
        cls_result, risk_result = _full_pipeline(db, "NTX-IND-00002")
        assert risk_result.risk_level == RiskLevel.LOW
        assert "no immediate action" in risk_result.recommended_action.lower()
    finally:
        db.close()


def test_scenario_c_is_critical_immediate_investigation():
    """Master plan: Scenario C -> Potential Industrial Fire, Risk: Critical, high historical deviation, Action: Immediate investigation."""
    db = SessionLocal()
    try:
        cls_result, risk_result = _full_pipeline(db, "NTX-IND-00003")
        assert risk_result.risk_level == RiskLevel.CRITICAL
        assert risk_result.risk_score > 75
        assert "immediate" in risk_result.recommended_action.lower()
    finally:
        db.close()


def test_risk_score_always_within_bounds():
    db = SessionLocal()
    try:
        events = db.execute(select(ThermalEvent)).scalars().all()
        for evt in events:
            _, risk_result = _full_pipeline(db, evt.event_id)
            assert 0 <= risk_result.risk_score <= 100
    finally:
        db.close()


def test_at_least_five_events_reach_critical():
    """Sanity check the risk engine, applied over the whole seeded dataset,
    actually reaches CRITICAL for the severe anomaly events (not just
    Scenario C alone)."""
    db = SessionLocal()
    try:
        events = db.execute(select(ThermalEvent)).scalars().all()
        critical_count = 0
        for evt in events:
            _, risk_result = _full_pipeline(db, evt.event_id)
            if risk_result.risk_level == RiskLevel.CRITICAL:
                critical_count += 1
        assert critical_count >= 5
    finally:
        db.close()


def test_components_are_fully_auditable():
    db = SessionLocal()
    try:
        _, risk_result = _full_pipeline(db, "NTX-IND-00003")
        assert "weighted_contributions" in risk_result.components
        total_weighted = sum(risk_result.components["weighted_contributions"].values())
        assert abs(total_weighted * 100 - risk_result.risk_score) < 1.0
    finally:
        db.close()
