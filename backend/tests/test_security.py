"""
Phase 14 security tests.

Rate limiting is tested by directly exercising the configured Limiter
against a fresh key, rather than firing 120+ real requests through
TestClient on every test run (slow, and shares state with other tests
hitting the same default key).
"""
from app.main import limiter


def test_rate_limiter_actually_trips_on_burst():
    """
    Behavioral check using an isolated FastAPI app + fresh Limiter (not
    the shared app-wide `limiter`), so this doesn't consume rate-limit
    budget from — or get polluted by — every other test hitting the real
    app's endpoints in the same process.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address

    isolated_limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
    isolated_app = FastAPI()
    isolated_app.state.limiter = isolated_limiter
    isolated_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    isolated_app.add_middleware(SlowAPIMiddleware)

    @isolated_app.get("/ping")
    def ping():
        return {"ok": True}

    test_client = TestClient(isolated_app)
    statuses = [test_client.get("/ping").status_code for _ in range(8)]
    assert 200 in statuses
    assert 429 in statuses


def test_rate_limiter_is_configured():
    assert limiter.enabled
    default_limit_group = limiter._default_limits[0]
    limits = list(default_limit_group)
    assert len(limits) == 1
    assert limits[0].limit.amount == 120
    assert limits[0].limit.GRANULARITY.name == "minute"


def test_env_file_is_gitignored():
    import subprocess
    from pathlib import Path

    backend_root = Path(__file__).resolve().parents[1]
    gitignore = (backend_root / ".gitignore").read_text()
    assert ".env" in gitignore


def test_cors_does_not_allow_wildcard_with_credentials():
    """allow_origins='*' combined with allow_credentials=True is a known
    misconfiguration that browsers actually reject anyway, but we should
    never rely on that — confirm we use an explicit origin list."""
    from app.core.config import get_settings

    settings = get_settings()
    assert "*" not in settings.CORS_ORIGINS


def test_firms_api_key_never_in_health_response():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    body = client.get("/api/health").json()
    assert "FIRMS_API_KEY" not in str(body)
