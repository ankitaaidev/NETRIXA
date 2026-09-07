"""
Pipeline orchestrator: the concrete implementation of the master plan's
architecture diagram —

    FIRMS/Demo Data -> thermal_events -> Geospatial Context ->
    Historical Intelligence -> AI Classification -> Risk Engine ->
    event_analysis -> alerts

This is what turns Phase 4's raw seeded rows into genuinely computed
intelligence. Nothing here is a fabricated result: every field written to
event_analysis is the direct output of the real modules built in Phases
5-8, run against the real data already in the database.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.geospatial.facility_proximity import nearest_facility
from app.geospatial.land_cover import resolve_land_cover
from app.ml.classifier import ClassifierFeatures, ThermalClassifier
from app.models.alert import Alert
from app.models.enums import AlertStatus, ProximityLevel, RiskLevel
from app.models.event_analysis import EventAnalysis
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.risk.risk_engine import compute_risk
from app.services.temporal_service import analyze_history

_classifier = ThermalClassifier()

# Alerts are generated for these risk levels — LOW/MEDIUM don't need one.
ALERT_WORTHY_LEVELS = {RiskLevel.HIGH, RiskLevel.CRITICAL}


def process_event(db: Session, event: ThermalEvent) -> EventAnalysis:
    """Runs one event through the full pipeline and upserts its
    event_analysis row. Does not commit — caller controls the transaction."""
    match = nearest_facility(db, event.latitude, event.longitude)
    lc = resolve_land_cover(
        event.land_cover, event.latitude, event.longitude,
        match.distance_m if match else None,
    )
    observations = db.execute(
        select(HistoricalObservation).where(HistoricalObservation.event_id == event.event_id)
    ).scalars().all()
    temporal = analyze_history(observations, event.brightness_temperature)

    features = ClassifierFeatures(
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
    classification_result = _classifier.predict(features)

    risk_result = compute_risk(
        z_score=temporal.z_score,
        proximity=match.proximity if match else ProximityLevel.NONE,
        persistence_score=temporal.persistence_score,
        spatial_change_score=temporal.spatial_change_score,
        classification=classification_result.classification,
        classification_confidence=classification_result.confidence,
    )

    existing = db.execute(
        select(EventAnalysis).where(EventAnalysis.event_id == event.event_id)
    ).scalar_one_or_none()

    explanation_json = [
        {"factor": f.factor, "value": f.value, "confirmed": f.confirmed, "description": f.description}
        for f in classification_result.explanation
    ]

    values = dict(
        classification=classification_result.classification,
        confidence=classification_result.confidence,
        probability_distribution=classification_result.probability_distribution,
        risk_score=risk_result.risk_score,
        risk_level=risk_result.risk_level,
        persistence_score=temporal.persistence_score,
        anomaly_score=round(min(abs(temporal.z_score) / 4.0, 1.0), 4),
        historical_deviation=temporal.current_deviation,
        industrial_proximity=match.proximity if match else ProximityLevel.NONE,
        spatial_change_score=temporal.spatial_change_score,
        explanation=explanation_json,
        recommended_action=risk_result.recommended_action,
        persistence=temporal.persistence,
        spatial_change=temporal.spatial_change,
        historical_mean=temporal.historical_mean,
        historical_std=temporal.historical_std,
        z_score=temporal.z_score,
        observations=temporal.observations,
        first_observed=temporal.first_observed,
        last_observed=temporal.last_observed,
        facility_name=match.facility.name if match else None,
        facility_distance=match.distance_m if match else None,
        facility_type=match.facility.facility_type if match else None,
    )

    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
        analysis = existing
    else:
        analysis = EventAnalysis(event_id=event.event_id, **values)
        db.add(analysis)

    db.flush()
    _sync_alert_for_event(db, event, analysis)
    return analysis


def _sync_alert_for_event(db: Session, event: ThermalEvent, analysis: EventAnalysis) -> None:
    """Creates an alert for HIGH/CRITICAL events if one doesn't already
    exist; leaves existing alerts (and their ACKNOWLEDGED/RESOLVED status)
    untouched on re-runs rather than duplicating or resetting them."""
    existing_alert = db.execute(
        select(Alert).where(Alert.event_id == event.event_id)
    ).scalar_one_or_none()

    if analysis.risk_level not in ALERT_WORTHY_LEVELS:
        return  # not alert-worthy; leave any existing alert as-is (analyst may have already acted on it)

    if existing_alert:
        return  # already have an alert for this event; don't duplicate or reset its status

    alert_id = f"ALT-{event.event_id.replace('NTX-', '')}"
    db.add(Alert(
        alert_id=alert_id,
        event_id=event.event_id,
        severity=analysis.risk_level,
        title=f"{analysis.classification.value} detected — {analysis.risk_level.value} risk",
        message=(
            f"Thermal anomaly at {event.state}, {event.district} classified as "
            f"{analysis.classification.value} with a risk score of {analysis.risk_score}/100. "
            f"{'Nearest facility: ' + analysis.facility_name + '.' if analysis.facility_name else ''}"
        ),
        status=AlertStatus.ACTIVE,
        recommended_action=analysis.recommended_action,
    ))


def run_pipeline_for_all_events(db: Session) -> dict:
    events = db.execute(select(ThermalEvent)).scalars().all()
    processed = 0
    for event in events:
        process_event(db, event)
        processed += 1
    db.commit()
    return {"processed": processed}


if __name__ == "__main__":
    from app.database.session import get_session_factory

    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        result = run_pipeline_for_all_events(session)
        print(f"Pipeline complete: {result}")
    finally:
        session.close()
