"""
GET /api/health

Reports the ACTUAL status of each subsystem. Nothing here is hard-coded
to "online" — every check either does real work (attempt a DB connection,
attempt an import) or explicitly reports why it can't yet be verified
(e.g. a later phase hasn't been implemented).

Status vocabulary used across checks:
  "online"         - verified working right now
  "demo"           - intentionally operating in demo/offline mode
  "not_configured" - no credentials/config provided (expected in demo mode)
  "unavailable"    - required library/service could not be reached
  "pending"        - subsystem not yet implemented in this build phase
"""
import importlib.util
import time

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


def _check_database() -> dict:
    settings = get_settings()
    if not settings.DATABASE_URL:
        return {
            "status": "not_configured",
            "detail": "DATABASE_URL not set (expected while DEMO_MODE=true and Phase 3 not yet applied).",
        }
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            try:
                postgis_version = conn.execute(text("SELECT postgis_version()")).scalar()
            except Exception:  # noqa: BLE001 - extension may not be enabled yet
                return {
                    "status": "unavailable",
                    "detail": "Connected to Postgres, but PostGIS extension is not enabled on this database.",
                }
        return {
            "status": "online",
            "detail": f"Connected. PostGIS {postgis_version}.",
        }
    except Exception as exc:  # noqa: BLE001 - we want to surface any connection failure
        return {"status": "unavailable", "detail": f"Connection failed: {exc.__class__.__name__}: {exc}"}


def _check_gis_engine() -> dict:
    missing = [pkg for pkg in ("geopandas", "shapely") if importlib.util.find_spec(pkg) is None]
    if missing:
        return {"status": "unavailable", "detail": f"Missing packages: {', '.join(missing)}."}
    return {"status": "online", "detail": "geopandas and shapely importable."}


def _check_ai_engine() -> dict:
    if importlib.util.find_spec("app.ml.classifier") is None:
        return {"status": "pending", "detail": "ThermalClassifier not yet implemented (Phase 7)."}
    try:
        from app.ml.classifier import ThermalClassifier

        ThermalClassifier()  # cheap instantiation check — no state, no I/O
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "detail": f"Classifier failed to initialize: {exc.__class__.__name__}: {exc}"}
    return {
        "status": "online",
        "detail": "Deterministic rule-based classifier loaded (no trained model — see app/ml/classifier.py docstring).",
    }


def _check_data_pipeline() -> dict:
    settings = get_settings()
    if importlib.util.find_spec("app.database.seed") is None:
        return {"status": "pending", "detail": "Demo data seed not yet implemented (Phase 4)."}
    if not settings.DATABASE_URL:
        return {"status": "demo" if settings.DEMO_MODE else "not_configured",
                "detail": "Seed module present; no database configured to check for seeded data."}
    try:
        from sqlalchemy import func, select

        from app.database.session import get_session_factory
        from app.models.event_analysis import EventAnalysis
        from app.models.thermal_event import ThermalEvent

        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            event_count = db.execute(select(func.count(ThermalEvent.event_id))).scalar() or 0
            analyzed_count = db.execute(select(func.count(EventAnalysis.id))).scalar() or 0
        finally:
            db.close()
        if event_count == 0:
            return {"status": "demo" if settings.DEMO_MODE else "not_configured",
                    "detail": "Seed module present but no events seeded yet — run `python -m app.database.seed`."}
        return {
            "status": "demo" if settings.DEMO_MODE else "online",
            "detail": f"{event_count} thermal events seeded, {analyzed_count} processed through the analysis pipeline.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "detail": f"Could not verify seeded data: {exc.__class__.__name__}: {exc}"}


def _check_satellite_feed() -> dict:
    from app.services.firms_service import get_firms_status

    status = get_firms_status()
    if status.demo_mode and not status.configured:
        return {"status": "demo", "detail": status.message}
    if not status.configured:
        return {"status": "not_configured", "detail": status.message}
    return {"status": "not_configured", "detail": status.message + " (live HTTP ingestion not implemented in this prototype build)"}


@router.get("/health")
def get_health():
    started = time.monotonic()
    checks = {
        "api": {"status": "online", "detail": "Request served successfully."},
        "database": _check_database(),
        "gis_engine": _check_gis_engine(),
        "ai_engine": _check_ai_engine(),
        "data_pipeline": _check_data_pipeline(),
        "satellite_feed": _check_satellite_feed(),
    }

    # Overall status is "ok" only if nothing reports a hard failure.
    # not_configured / demo / pending are acceptable in a prototype and
    # don't count as failures on their own.
    hard_failure_statuses = {"unavailable"}
    overall = "degraded" if any(c["status"] in hard_failure_statuses for c in checks.values()) else "ok"

    return {
        "status": overall,
        "demo_mode": get_settings().DEMO_MODE,
        "checks": checks,
        "response_time_ms": round((time.monotonic() - started) * 1000, 2),
    }
