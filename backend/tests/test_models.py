"""
Integration tests against a REAL PostgreSQL + PostGIS instance (not mocks).

Requires DATABASE_URL to be set (see backend/.env) and the schema to be
migrated (`alembic upgrade head`, or app.database.init_db.init_db()).

Each test runs inside a transaction that's rolled back afterward, so the
database is left clean regardless of pass/fail.
"""
from datetime import date, datetime, timezone

import pytest
from geoalchemy2.shape import to_shape

from app.database.geo_listeners import register_geo_listeners
from app.database.session import get_engine, get_session_factory
from app.models.alert import Alert
from app.models.analyst_feedback import AnalystFeedback
from app.models.enums import (
    AlertStatus,
    ClassificationType,
    FeedbackDecision,
    PersistenceType,
    ProximityLevel,
    RiskLevel,
    SpatialChangeLevel,
)
from app.models.event_analysis import EventAnalysis
from app.models.facility import Facility
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent

register_geo_listeners()


@pytest.fixture
def db_session():
    """Yields a session bound to a SAVEPOINT-nested transaction that is
    always rolled back, so tests never leave rows behind."""
    engine = get_engine()
    connection = engine.connect()
    trans = connection.begin()
    SessionLocal = get_session_factory()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    trans.rollback()
    connection.close()


def test_thermal_event_insert_and_geom_autopopulate(db_session):
    evt = ThermalEvent(
        event_id="NTX-TEST-00001",
        latitude=22.57,
        longitude=88.36,
        detection_time=datetime(2026, 9, 4, 3, 42, tzinfo=timezone.utc),
        brightness_temperature=412.0,
        frp=68.4,
        confidence=87.0,
        satellite="AQUA",
        instrument="MODIS",
        source="DEMO",
        state="West Bengal",
        district="Howrah",
    )
    db_session.add(evt)
    db_session.flush()  # triggers before_insert listener without committing

    fetched = db_session.get(ThermalEvent, "NTX-TEST-00001")
    assert fetched is not None
    assert fetched.geom is not None

    point = to_shape(fetched.geom)
    # geom stores (lon, lat) — verify it matches what we set, not swapped.
    assert round(point.x, 2) == 88.36
    assert round(point.y, 2) == 22.57


def test_thermal_event_id_is_the_only_identifier(db_session):
    """No numeric routing id column should exist — event_id is the sole PK."""
    mapper = ThermalEvent.__mapper__
    pk_columns = [c.name for c in mapper.primary_key]
    assert pk_columns == ["event_id"]
    assert "id" not in [c.name for c in mapper.columns]


def test_event_analysis_relationship_and_json_fields(db_session):
    evt = ThermalEvent(
        event_id="NTX-TEST-00002",
        latitude=21.18,
        longitude=72.81,
        detection_time=datetime(2026, 9, 4, 2, 15, tzinfo=timezone.utc),
        brightness_temperature=341.0,
        frp=42.1,
        confidence=91.0,
        satellite="TERRA",
        instrument="MODIS",
    )
    db_session.add(evt)
    db_session.flush()

    analysis = EventAnalysis(
        event_id="NTX-TEST-00002",
        classification=ClassificationType.PERSISTENT_INDUSTRIAL_THERMAL_SOURCE,
        confidence=92.0,
        probability_distribution={"Persistent Industrial Thermal Source": 0.92, "Gas Flare": 0.04, "Other": 0.04},
        risk_score=18,
        risk_level=RiskLevel.LOW,
        persistence_score=0.05,
        anomaly_score=0.06,
        historical_deviation=1.0,
        industrial_proximity=ProximityLevel.HIGH,
        spatial_change_score=0.02,
        explanation=[{"factor": "Persistent facility pattern", "value": "LOW", "confirmed": True, "description": "Stable signal"}],
        recommended_action="No action — normal LNG terminal operation",
        persistence=PersistenceType.NORMAL_PERSISTENT,
        spatial_change=SpatialChangeLevel.STABLE,
        historical_mean=340.0,
        historical_std=12.4,
        z_score=0.08,
        observations=142,
        first_observed=date(2026, 1, 12),
        last_observed=date(2026, 9, 4),
        facility_name="Hazira LNG Terminal",
        facility_distance=95.0,
        facility_type="LNG Terminal",
    )
    db_session.add(analysis)
    db_session.flush()

    db_session.refresh(evt)
    assert evt.analysis is not None
    assert evt.analysis.classification == ClassificationType.PERSISTENT_INDUSTRIAL_THERMAL_SOURCE
    assert evt.analysis.probability_distribution["Gas Flare"] == 0.04
    assert evt.analysis.explanation[0]["factor"] == "Persistent facility pattern"


def test_event_analysis_unique_constraint_on_event_id(db_session):
    evt = ThermalEvent(
        event_id="NTX-TEST-00003",
        latitude=13.08,
        longitude=80.27,
        detection_time=datetime.now(timezone.utc),
        brightness_temperature=402.0,
        frp=58.9,
        confidence=80.0,
        satellite="AQUA",
        instrument="MODIS",
    )
    db_session.add(evt)
    db_session.flush()

    def make_analysis():
        return EventAnalysis(
            event_id="NTX-TEST-00003",
            classification=ClassificationType.INDUSTRIAL_FIRE,
            confidence=80.0,
            probability_distribution={"Industrial Fire": 0.8},
            risk_score=85,
            risk_level=RiskLevel.CRITICAL,
            persistence_score=0.9,
            anomaly_score=0.91,
            historical_deviation=344.0,
            industrial_proximity=ProximityLevel.HIGH,
            spatial_change_score=0.9,
            explanation=[],
            recommended_action="Immediate investigation",
            persistence=PersistenceType.SUDDEN_EVENT,
            spatial_change=SpatialChangeLevel.HIGH,
            observations=1,
        )

    db_session.add(make_analysis())
    db_session.flush()

    # Use a SAVEPOINT so the expected IntegrityError doesn't poison the
    # outer test-transaction the fixture relies on for cleanup.
    savepoint = db_session.begin_nested()
    db_session.add(make_analysis())
    with pytest.raises(Exception):
        db_session.flush()
    savepoint.rollback()


def test_historical_observation_unique_per_event_date(db_session):
    evt = ThermalEvent(
        event_id="NTX-TEST-00004",
        latitude=20.0,
        longitude=80.0,
        detection_time=datetime.now(timezone.utc),
        brightness_temperature=300.0,
        frp=10.0,
        confidence=70.0,
        satellite="TERRA",
        instrument="MODIS",
    )
    db_session.add(evt)
    db_session.flush()

    obs1 = HistoricalObservation(event_id="NTX-TEST-00004", obs_date=date(2026, 9, 1), intensity=300.0, frp=10.0)
    db_session.add(obs1)
    db_session.flush()

    savepoint = db_session.begin_nested()
    obs_dup = HistoricalObservation(event_id="NTX-TEST-00004", obs_date=date(2026, 9, 1), intensity=305.0, frp=11.0)
    db_session.add(obs_dup)
    with pytest.raises(Exception):
        db_session.flush()
    savepoint.rollback()


def test_alert_and_feedback_cascade_relationships(db_session):
    evt = ThermalEvent(
        event_id="NTX-TEST-00005",
        latitude=19.08,
        longitude=72.88,
        detection_time=datetime.now(timezone.utc),
        brightness_temperature=395.0,
        frp=50.0,
        confidence=85.0,
        satellite="AQUA",
        instrument="MODIS",
    )
    db_session.add(evt)
    db_session.flush()

    alert = Alert(
        alert_id="a-test-1",
        event_id="NTX-TEST-00005",
        severity=RiskLevel.CRITICAL,
        title="Test alert",
        message="Test message",
        status=AlertStatus.ACTIVE,
        recommended_action="Immediate field investigation.",
    )
    feedback = AnalystFeedback(
        event_id="NTX-TEST-00005",
        decision=FeedbackDecision.CONFIRMED,
        analyst_note="Verified via field report.",
    )
    db_session.add_all([alert, feedback])
    db_session.flush()

    db_session.refresh(evt)
    assert len(evt.alerts) == 1
    assert evt.alerts[0].severity == RiskLevel.CRITICAL
    assert len(evt.feedback) == 1
    assert evt.feedback[0].decision == FeedbackDecision.CONFIRMED


def test_facility_geom_autopopulate(db_session):
    fac = Facility(
        facility_id="FAC-TEST-001",
        name="Test Refinery",
        facility_type="Refinery",
        latitude=22.42,
        longitude=70.05,
        state="Gujarat",
        district="Jamnagar",
    )
    db_session.add(fac)
    db_session.flush()

    fetched = db_session.get(Facility, "FAC-TEST-001")
    assert fetched.geom is not None
    point = to_shape(fetched.geom)
    assert round(point.x, 2) == 70.05
    assert round(point.y, 2) == 22.42


def test_spatial_nearest_facility_query(db_session):
    """Sanity check that PostGIS spatial functions work end-to-end through
    our models — this is what Phase 5's geospatial service will build on."""
    from sqlalchemy import func, select

    fac = Facility(
        facility_id="FAC-TEST-002",
        name="Nearby Steel Plant",
        facility_type="Steel Plant",
        latitude=22.57,
        longitude=88.36,
        state="West Bengal",
        district="Howrah",
    )
    db_session.add(fac)
    db_session.flush()

    evt = ThermalEvent(
        event_id="NTX-TEST-00006",
        latitude=22.5701,  # ~a few dozen meters away
        longitude=88.3601,
        detection_time=datetime.now(timezone.utc),
        brightness_temperature=400.0,
        frp=60.0,
        confidence=85.0,
        satellite="AQUA",
        instrument="MODIS",
    )
    db_session.add(evt)
    db_session.flush()

    # ST_DistanceSphere gives a great-circle distance in meters directly
    # from two geometry columns — this is what Phase 5's nearest-facility
    # query will rely on.
    distance_m = db_session.execute(
        select(func.ST_DistanceSphere(fac.geom, evt.geom))
    ).scalar()
    assert distance_m is not None
    assert distance_m < 50  # a few tens of meters apart, as constructed
