from collections import Counter

from sqlalchemy import and_, select

from app.database.session import get_session_factory
from app.models.thermal_event import ThermalEvent
from app.services.pipeline import process_event


db = get_session_factory()()

events = db.execute(
    select(ThermalEvent).where(
        and_(
            ThermalEvent.source == "FIRMS",
            ThermalEvent.latitude >= 15.1,
            ThermalEvent.latitude < 15.2,
            ThermalEvent.longitude >= 76.6,
            ThermalEvent.longitude < 76.7,
        )
    )
).scalars().all()

classifications = Counter()
risks = Counter()
facility_matches = 0

for event in events:
    analysis = process_event(db, event)

    classifications[analysis.classification.value] += 1
    risks[analysis.risk_level.value] += 1

    if analysis.facility_distance is not None:
        facility_matches += 1

db.rollback()

print("Events analyzed:", len(events))
print("Facility matches:", facility_matches)

print("\nClassifications:")
for name, count in classifications.most_common():
    print(f"  {name}: {count}")

print("\nRisk levels:")
for name, count in risks.most_common():
    print(f"  {name}: {count}")