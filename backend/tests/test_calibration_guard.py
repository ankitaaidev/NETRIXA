"""
End-to-end calibration guard: runs the full geospatial -> temporal ->
classifier pipeline over every seeded event and checks the predicted
classification matches the category the seed generator intended.

This is deliberately a strict, whole-dataset test (not just the 3 named
scenarios) because per-category threshold tuning in classifier.py or
seed.py can silently break agreement for categories no other test
directly checks. If this test fails after a change, the fix is to adjust
either the seed's raw feature ranges or the classifier's scoring
thresholds until they agree again — not to loosen this test.
"""
from collections import defaultdict

from sqlalchemy import select

from app.database.session import get_session_factory
from app.database.seed import generate_event_specs
from app.geospatial.facility_proximity import nearest_facility
from app.geospatial.land_cover import resolve_land_cover
from app.ml.classifier import ClassifierFeatures, ThermalClassifier
from app.models.enums import ProximityLevel
from app.models.facility import Facility
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.services.temporal_service import analyze_history

SessionLocal = get_session_factory()
classifier = ThermalClassifier()

# Full agreement is achievable and is what we've calibrated to; keep the
# bar at 100% intentionally so any regression is caught immediately.
MIN_AGREEMENT = 1.0


def test_full_dataset_classification_agreement():
    db = SessionLocal()
    try:
        facilities = db.execute(select(Facility)).scalars().all()
        specs = generate_event_specs(facilities)
        intended_by_id = {s.event_id: s.category for s in specs}

        events = db.execute(select(ThermalEvent)).scalars().all()
        assert len(events) > 0, "No seeded events found — run app.database.seed first."

        agree = 0
        total = 0
        mismatches = defaultdict(list)

        for evt in events:
            intended = intended_by_id.get(evt.event_id)
            if not intended:
                continue

            match = nearest_facility(db, evt.latitude, evt.longitude)
            lc = resolve_land_cover(
                evt.land_cover, evt.latitude, evt.longitude,
                match.distance_m if match else None,
            )
            obs = db.execute(
                select(HistoricalObservation).where(HistoricalObservation.event_id == evt.event_id)
            ).scalars().all()
            temporal = analyze_history(obs, evt.brightness_temperature)

            features = ClassifierFeatures(
                brightness_temperature=evt.brightness_temperature,
                frp=evt.frp,
                confidence=evt.confidence,
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
            result = classifier.predict(features)
            total += 1
            if result.classification.value == intended:
                agree += 1
            else:
                mismatches[intended].append((evt.event_id, result.classification.value))

        agreement = agree / total
        assert agreement >= MIN_AGREEMENT, (
            f"Classification agreement dropped to {agreement:.1%} ({agree}/{total}). "
            f"Mismatches by intended category: {dict(mismatches)}"
        )
    finally:
        db.close()
