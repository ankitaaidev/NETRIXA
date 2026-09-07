from sqlalchemy import select

from app.database.session import get_session_factory
from app.models.alert import Alert
from app.models.enums import AlertStatus, RiskLevel
from app.models.event_analysis import EventAnalysis
from app.models.thermal_event import ThermalEvent
from app.services.pipeline import process_event, run_pipeline_for_all_events

SessionLocal = get_session_factory()


def test_all_events_have_analysis_after_pipeline_run():
    db = SessionLocal()
    try:
        analysis_count = len(db.execute(select(EventAnalysis)).scalars().all())
        total_events = len(db.execute(select(ThermalEvent)).scalars().all())
        assert analysis_count == total_events
        assert total_events > 0
    finally:
        db.close()


def test_named_scenarios_match_master_plan_exactly():
    db = SessionLocal()
    try:
        a = db.execute(select(EventAnalysis).where(EventAnalysis.event_id == "NTX-IND-00001")).scalar_one()
        b = db.execute(select(EventAnalysis).where(EventAnalysis.event_id == "NTX-IND-00002")).scalar_one()
        c = db.execute(select(EventAnalysis).where(EventAnalysis.event_id == "NTX-IND-00003")).scalar_one()

        assert a.risk_level == RiskLevel.LOW
        assert "observe" in a.recommended_action.lower()

        assert b.risk_level == RiskLevel.LOW
        assert "no immediate action" in b.recommended_action.lower()

        assert c.risk_level == RiskLevel.CRITICAL
        assert "immediate" in c.recommended_action.lower()
    finally:
        db.close()


def test_alerts_only_exist_for_high_and_critical():
    db = SessionLocal()
    try:
        alerts = db.execute(select(Alert)).scalars().all()
        assert len(alerts) > 0
        for alert in alerts:
            assert alert.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    finally:
        db.close()


def test_alert_ids_are_unique_across_prefixes():
    """Regression test for the ALT-00003 collision bug between
    NTX-IND-00003 and NTX-WLD-00003."""
    db = SessionLocal()
    try:
        alert_ids = db.execute(select(Alert.alert_id)).scalars().all()
        assert len(alert_ids) == len(set(alert_ids))
    finally:
        db.close()


def test_pipeline_rerun_does_not_duplicate_alerts():
    db = SessionLocal()
    try:
        before = len(db.execute(select(Alert)).scalars().all())
        run_pipeline_for_all_events(db)
        after = len(db.execute(select(Alert)).scalars().all())
        assert before == after
    finally:
        db.close()


def test_pipeline_rerun_preserves_acknowledged_alert_status():
    """Re-running the pipeline must not silently reset an analyst's
    acknowledgment of an existing alert."""
    db = SessionLocal()
    try:
        alert = db.execute(select(Alert).limit(1)).scalar_one()
        alert.status = AlertStatus.ACKNOWLEDGED
        db.commit()

        run_pipeline_for_all_events(db)

        db.refresh(alert)
        assert alert.status == AlertStatus.ACKNOWLEDGED
    finally:
        db.close()


def test_at_least_ten_persistent_sources_in_final_analysis():
    """Master plan requirement: at least 10 persistent sources in the demo dataset."""
    db = SessionLocal()
    try:
        from app.models.enums import PersistenceType
        count = len(db.execute(
            select(EventAnalysis).where(EventAnalysis.persistence == PersistenceType.NORMAL_PERSISTENT)
        ).scalars().all())
        assert count >= 10
    finally:
        db.close()
