from datetime import datetime, timezone

from app.database.session import session_scope
from app.models.thermal_event import ThermalEvent


event = ThermalEvent(
    event_id="NTX-TEST-001",
    latitude=22.57,
    longitude=88.36,
    geom="SRID=4326;POINT(88.36 22.57)",
    detection_time=datetime.now(timezone.utc),
    brightness_temperature=340.0,
    frp=10.0,
    confidence=70.0,
    satellite="TEST",
    instrument="VIIRS",
    source="TEST",
)

with session_scope() as db:
    db.add(event)
    db.flush()

print("Geometry insert: OK")