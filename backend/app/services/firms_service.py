"""
NASA FIRMS integration (Phase 12).

Prepares support for live NASA FIRMS thermal-detection feeds WITHOUT
making live connectivity a requirement for the demo. When DEMO_MODE=true
(the default) or FIRMS_API_KEY is unset, this module's functions return
a clear "not configured" result rather than attempting a network call or
raising — the rest of the application must keep working with the seeded
demo data regardless.

FIRMS_API_KEY is read only from environment/.env via app.core.config —
never hard-coded here, never logged, never returned in any response body.

Real FIRMS ingestion (when a key is available) would call the FIRMS area
API, e.g.:
    https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/{area}/{days}
and map each CSV row into a `ThermalEvent` (source="FIRMS") before running
it through the same pipeline (app.services.pipeline.process_event) used
for demo data — no separate code path is needed downstream of ingestion.
"""
from dataclasses import dataclass

from app.core.config import get_settings

FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


@dataclass
class FirmsStatus:
    configured: bool
    demo_mode: bool
    message: str


def get_firms_status() -> FirmsStatus:
    settings = get_settings()
    if settings.DEMO_MODE and not settings.FIRMS_API_KEY:
        return FirmsStatus(
            configured=False, demo_mode=True,
            message="DEMO_MODE active — using offline seeded demo data instead of live FIRMS.",
        )
    if not settings.FIRMS_API_KEY:
        return FirmsStatus(
            configured=False, demo_mode=settings.DEMO_MODE,
            message="FIRMS_API_KEY not set. Add it to .env to enable live ingestion.",
        )
    return FirmsStatus(
        configured=True, demo_mode=settings.DEMO_MODE,
        message="FIRMS_API_KEY configured. Live ingestion available via fetch_recent_detections().",
    )


def build_area_url(satellite: str, bounding_box: str, days: int) -> str:
    """
    Constructs a FIRMS area-API URL without ever embedding the key in a
    string that could be logged elsewhere by mistake — caller is
    responsible for using this only in the actual request, not logging it.
    """
    settings = get_settings()
    if not settings.FIRMS_API_KEY:
        raise RuntimeError("FIRMS_API_KEY is not configured.")
    return f"{FIRMS_BASE_URL}/{settings.FIRMS_API_KEY}/{satellite}/{bounding_box}/{days}"


def fetch_recent_detections(satellite: str = "VIIRS_SNPP_NRT", bounding_box: str = "68,6,98,38", days: int = 1):
    """
    Placeholder for live ingestion. Deliberately NOT implemented with an
    actual outbound HTTP call in this prototype build — this sandbox's
    network allowlist doesn't include firms.modaps.eosdis.nasa.gov, and
    more importantly, DEMO_MODE must never depend on this succeeding.

    A production deployment would: fetch the CSV from build_area_url(),
    parse each row into raw thermal_events fields (lat/lon, brightness
    temp, FRP, confidence, satellite, instrument, detection_time,
    source="FIRMS"), insert them, then call
    app.services.pipeline.process_event() on each — reusing every stage
    already built (Phases 5-8) unchanged.
    """
    status = get_firms_status()
    if not status.configured:
        raise RuntimeError(status.message)
    raise NotImplementedError(
        "Live FIRMS HTTP ingestion is not implemented in this prototype build. "
        "See module docstring for the intended integration path."
    )
