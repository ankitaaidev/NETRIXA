from app.database.session import session_scope
from app.models.thermal_event import ThermalEvent
from sqlalchemy import delete

with session_scope() as db:
    db.execute(
        delete(ThermalEvent).where(
            ThermalEvent.event_id == "NTX-TEST-001"
        )
    )

print("Test event removed")