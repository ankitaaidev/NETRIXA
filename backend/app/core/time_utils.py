"""
Provides a single "reference now" used anywhere activity is computed
relative to time (e.g. facility 30d/90d thermal activity). In DEMO_MODE
this is pinned to the same fixed date the demo data was generated
relative to (app.database.seed.DEMO_TODAY), so numbers stay stable no
matter when the demo is actually run. Outside demo mode it's real time.
"""
from datetime import datetime, time, timezone

from app.core.config import get_settings


def reference_now() -> datetime:
    settings = get_settings()
    if settings.DEMO_MODE:
        anchor_date = datetime.strptime(settings.DEMO_ANCHOR_DATE, "%Y-%m-%d").date()
        return datetime.combine(anchor_date, time(23, 59, 59), tzinfo=timezone.utc)
    return datetime.now(timezone.utc)
