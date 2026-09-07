from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api import alerts, dashboard, events, facilities, health, map as map_api, priority, reports
from app.core.config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="NETRIXA API",
    description="AI-Powered Thermal Intelligence & Early-Warning System — SIH 2026 (PS #26162)",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(priority.router, prefix="/api", tags=["priority"])
app.include_router(facilities.router, prefix="/api", tags=["facilities"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(map_api.router, prefix="/api", tags=["map"])


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "status": "running", "demo_mode": settings.DEMO_MODE}
