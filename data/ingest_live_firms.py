import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import select

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Always load the backend .env file.
os.chdir(BACKEND_DIR)

from app.database.session import session_scope
from app.models.thermal_event import ThermalEvent


INPUT_FILE = Path(__file__).resolve().parents[1] / "data" / "processed" / "live_firms_india.csv"


def main():
    print("=" * 60)
    print("NETRIXA LIVE FIRMS - DATABASE INGESTION")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)

    print(f"Live India detections loaded: {len(df)}")

    if df.empty:
        print("No India detections to insert.")
        return

    with session_scope() as db:
        existing_count = db.query(ThermalEvent).count()

        print(f"Existing database events: {existing_count}")

        # Find the highest existing FIRMS event number.
        max_number = -1

        existing_ids = db.execute(
            select(ThermalEvent.event_id).where(
                ThermalEvent.event_id.like("NTX-FIRMS-%")
            )
        ).scalars().all()

        for event_id in existing_ids:
            try:
                number = int(event_id.split("-")[-1])
                max_number = max(max_number, number)
            except (ValueError, AttributeError):
                continue

        next_number = max_number + 1

        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            latitude = float(row["latitude"])
            longitude = float(row["longitude"])

            # FIRMS acquisition time is HHMM.
            acq_time_value = int(float(row["acq_time"]))
            hhmm = f"{acq_time_value:04d}"

            detection_time = pd.to_datetime(
                f"{row['acq_date']} {hhmm}",
                format="%Y-%m-%d %H%M",
                utc=True,
            ).to_pydatetime()

            satellite = str(row["satellite"])
            instrument = str(row["instrument"])

            brightness_temperature = float(row["bright_ti4"])
            frp = float(row["frp"])
            confidence_value = str(row["confidence"]).strip().lower()

            confidence_map = {
                "l": 40.0,
                "n": 70.0,
                "h": 90.0,
            }

            if confidence_value in confidence_map:
                confidence = confidence_map[confidence_value]
            else:
                confidence = float(confidence_value)
            # Check whether this FIRMS detection already exists.
            existing = db.execute(
                select(ThermalEvent).where(
                    ThermalEvent.latitude == latitude,
                    ThermalEvent.longitude == longitude,
                    ThermalEvent.detection_time == detection_time,
                    ThermalEvent.satellite == satellite,
                )
            ).scalars().first()

            if existing:
                skipped += 1
                continue

            event_id = f"NTX-FIRMS-{next_number:06d}"
            next_number += 1

            event = ThermalEvent(
                event_id=event_id,
                latitude=latitude,
                longitude=longitude,
                geom=f"SRID=4326;POINT({longitude} {latitude})",
                detection_time=detection_time,
                brightness_temperature=brightness_temperature,
                frp=frp,
                confidence=confidence,
                satellite=satellite,
                instrument=instrument,
                source="FIRMS",
            )

            db.add(event)
            inserted += 1

        print()
        print("=" * 60)
        print("INGESTION RESULT")
        print("=" * 60)
        print(f"Input detections:     {len(df)}")
        print(f"New events inserted:  {inserted}")
        print(f"Duplicates skipped:   {skipped}")
        print(f"Database total:       {existing_count + inserted}")


if __name__ == "__main__":
    main()