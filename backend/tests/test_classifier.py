from sqlalchemy import select

from app.database.session import get_session_factory
from app.geospatial.facility_proximity import nearest_facility
from app.geospatial.land_cover import land_cover_context
from app.ml.classifier import ClassifierFeatures, ThermalClassifier
from app.models.enums import ClassificationType, ProximityLevel
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.services.temporal_service import analyze_history

SessionLocal = get_session_factory()
classifier = ThermalClassifier()


def _build_features(db, event: ThermalEvent) -> ClassifierFeatures:
    match = nearest_facility(db, event.latitude, event.longitude)
    lc = land_cover_context(event.latitude, event.longitude, match.distance_m if match else None)
    obs = db.execute(
        select(HistoricalObservation).where(HistoricalObservation.event_id == event.event_id)
    ).scalars().all()
    temporal = analyze_history(obs, event.brightness_temperature)

    return ClassifierFeatures(
        brightness_temperature=event.brightness_temperature,
        frp=event.frp,
        confidence=event.confidence,
        facility_distance_m=match.distance_m if match else None,
        facility_proximity=match.proximity if match else ProximityLevel.NONE,
        land_cover=lc["land_cover"],
        historical_mean=temporal.historical_mean,
        historical_std=temporal.historical_std,
        z_score=temporal.z_score,
        persistence=temporal.persistence,
        recurrence_rate=temporal.recurrence_rate,
        observations=temporal.observations,
    )


def test_scenario_a_classifies_as_persistent_industrial_thermal_source():
    db = SessionLocal()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00001")
        features = _build_features(db, evt)
        result = classifier.predict(features)
        assert result.classification == ClassificationType.PERSISTENT_INDUSTRIAL_THERMAL_SOURCE
        assert result.confidence > 0
        assert abs(sum(result.probability_distribution.values()) - 1.0) < 0.01
    finally:
        db.close()


def test_scenario_b_classifies_as_agricultural_burning():
    db = SessionLocal()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00002")
        features = _build_features(db, evt)
        result = classifier.predict(features)
        assert result.classification == ClassificationType.AGRICULTURAL_BURNING
    finally:
        db.close()


def test_scenario_c_classifies_as_potential_industrial_fire():
    db = SessionLocal()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00003")
        features = _build_features(db, evt)
        result = classifier.predict(features)
        assert result.classification == ClassificationType.POTENTIAL_INDUSTRIAL_FIRE
        # explanation must cite the real deviation, not a canned string
        assert any("historical" in f.factor.lower() for f in result.explanation)
    finally:
        db.close()


def test_probability_distribution_covers_all_classes():
    db = SessionLocal()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00001")
        features = _build_features(db, evt)
        result = classifier.predict(features)
        assert len(result.probability_distribution) == 8
        assert all(0.0 <= p <= 1.0 for p in result.probability_distribution.values())
    finally:
        db.close()


def test_low_confidence_unclassifiable_event_falls_back_to_unknown():
    """A synthetic low-confidence, mixed-land-cover, no-facility event should
    honestly resolve to Unknown rather than a confident guess."""
    features = ClassifierFeatures(
        brightness_temperature=310.0, frp=8.0, confidence=42.0,
        facility_distance_m=None, facility_proximity=ProximityLevel.NONE,
        land_cover="Mixed/Unclassified", historical_mean=308.0, historical_std=10.0,
        z_score=0.2, persistence=__import__("app.models.enums", fromlist=["PersistenceType"]).PersistenceType.UNKNOWN,
        recurrence_rate=0.0, observations=2,
    )
    result = classifier.predict(features)
    assert result.classification == ClassificationType.UNKNOWN


def test_wildfire_event_classifies_correctly():
    db = SessionLocal()
    try:
        wildfire_evt = db.execute(
            select(ThermalEvent).where(ThermalEvent.event_id.like("NTX-WLD-%")).limit(1)
        ).scalar_one()
        features = _build_features(db, wildfire_evt)
        result = classifier.predict(features)
        assert result.classification == ClassificationType.WILDFIRE
    finally:
        db.close()


def test_never_claims_model_accuracy_in_explanation():
    """Guard against ever slipping a fabricated accuracy claim into output text."""
    db = SessionLocal()
    try:
        evt = db.get(ThermalEvent, "NTX-IND-00003")
        features = _build_features(db, evt)
        result = classifier.predict(features)
        for factor in result.explanation:
            assert "%" not in factor.description or "accuracy" not in factor.description.lower()
            assert "accurate" not in factor.description.lower()
    finally:
        db.close()
