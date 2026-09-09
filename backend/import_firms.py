from pathlib import Path

import pandas as pd
from sqlalchemy import select

from app.database.session import session_scope
from app.models.thermal_event import ThermalEvent


CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "processed"
    / "thermal_events_india.csv"
)


def build_event_id(index: int) -> str:
    return f"NTX-FIRMS-{index:06d}"


def parse_confidence(value) -> float:
    if pd.isna(value):
        return 0.0

    text = str(value).strip().lower()

    # FIRMS categorical confidence:
    # l = low, n = nominal, h = high
    if text == "l":
        return 40.0
    if text == "n":
        return 70.0
    if text == "h":
        return 90.0

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"FIRMS CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    required = [
        "latitude",
        "longitude",
        "brightness",
        "frp",
        "confidence",
        "satellite",
        "instrument",
        "acq_datetime",
    ]

    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    imported = 0
    skipped = 0

    with session_scope() as db:
        for index, row in df.iterrows():
            event_id = build_event_id(index + 1)

            existing = db.scalar(
                select(ThermalEvent).where(
                    ThermalEvent.event_id == event_id
                )
            )

            if existing:
                skipped += 1
                continue

            latitude = float(row["latitude"])
            longitude = float(row["longitude"])
            brightness = float(row["brightness"])
            frp = float(row["frp"])
            confidence = parse_confidence(row["confidence"])

            detection_time = pd.to_datetime(
                row["acq_datetime"],
                utc=True,
            ).to_pydatetime()

            event = ThermalEvent(
                event_id=event_id,
                latitude=latitude,
                longitude=longitude,
                geom=f"SRID=4326;POINT({longitude} {latitude})",
                detection_time=detection_time,
                brightness_temperature=brightness,
                frp=frp,
                confidence=confidence,
                satellite=str(row["satellite"]),
                instrument=str(row["instrument"]),
                source="FIRMS",
            )

            db.add(event)
            imported += 1

        print(f"Imported: {imported}")
        print(f"Skipped existing: {skipped}")
        print(f"Total CSV rows: {len(df)}")


if __name__ == "__main__":
    main()