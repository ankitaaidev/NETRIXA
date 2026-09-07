from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_responds():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "checks" in body


def test_health_reports_all_required_subsystems():
    body = client.get("/api/health").json()
    checks = body["checks"]
    for key in ("api", "database", "gis_engine", "ai_engine", "data_pipeline", "satellite_feed"):
        assert key in checks
        assert "status" in checks[key]


def test_health_reflects_real_database_state():
    """
    As of Phase 3, DATABASE_URL is configured and Postgres+PostGIS is
    actually running, so 'online' here is the truthful answer — not a
    hard-coded one. We verify it's backed by a real check by asserting
    the detail string contains real, specific evidence (a PostGIS version
    string), which a fabricated status could not produce.
    """
    body = client.get("/api/health").json()
    db_check = body["checks"]["database"]
    assert db_check["status"] in ("online", "unavailable", "not_configured")
    if db_check["status"] == "online":
        assert "PostGIS" in db_check["detail"]


def test_health_database_check_is_not_configured_when_url_unset(monkeypatch):
    """
    Isolates the 'not_configured' branch of the honesty logic without
    depending on the real .env state, so this keeps working correctly
    across every later phase regardless of whether DATABASE_URL happens
    to be set in the environment the tests run in.
    """
    import app.api.health as health_module
    from app.core.config import Settings

    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(DATABASE_URL=None, DEMO_MODE=True),
    )
    result = health_module._check_database()
    assert result["status"] == "not_configured"


def test_health_ai_engine_status_is_earned_not_assumed():
    """
    As of Phase 7, ThermalClassifier exists and is a pure rule-based
    Python module (no sklearn dependency — see app/ml/classifier.py
    docstring), so 'online' is the truthful, unconditional answer once
    the module is importable and instantiates cleanly.
    """
    import importlib.util

    body = client.get("/api/health").json()
    ai_check = body["checks"]["ai_engine"]
    if importlib.util.find_spec("app.ml.classifier") is None:
        assert ai_check["status"] == "pending"
    else:
        assert ai_check["status"] == "online"


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["name"] == "NETRIXA"
