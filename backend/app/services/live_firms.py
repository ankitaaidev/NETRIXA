"""
Live NASA FIRMS ingestion service.

Fetches recent VIIRS detections, keeps only detections inside India,
inserts new events into PostGIS, and runs the NETRIXA analysis pipeline.
"""
import asyncio
import io
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from sqlalchemy import select

from app.core.config import get_settings
from app.database.session import session_scope
from app.models.thermal_event import ThermalEvent
from app.services.pipeline import process_event


WEST = 68
SOUTH = 6
EAST = 98
NORTH = 36

SOURCES = [
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT",
]

BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Cache the India boundary so we do NOT query OSM every 10 minutes.
BOUNDARY_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "raw"
    / "boundaries"
    / "india.geojson"
)

SYNC_INTERVAL_SECONDS = 600  # 10 minutes


def load_india_boundary():
    """Load the cached India boundary."""

    if not BOUNDARY_FILE.exists():
        raise FileNotFoundError(
            f"India boundary not found: {BOUNDARY_FILE}"
        )

    india = gpd.read_file(BOUNDARY_FILE)

    if india.empty:
        raise RuntimeError("India boundary file is empty.")

    india = india.to_crs("EPSG:4326")

    return india.geometry.union_all()


def fetch_source(source: str, api_key: str) -> pd.DataFrame:
    """Fetch the most recent FIRMS detections for one satellite."""

    url = (
        f"{BASE_URL}/{api_key}/"
        f"{source}/{WEST},{SOUTH},{EAST},{NORTH}/1"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    if not response.text.strip():
        return pd.DataFrame()

    return pd.read_csv(io.StringIO(response.text))


def filter_india(df: pd.DataFrame, india_geometry) -> pd.DataFrame:
    """Keep only detections inside the actual India boundary."""

    if df.empty:
        return df

    points = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(
            df["longitude"],
            df["latitude"],
        ),
        crs="EPSG:4326",
    )

    inside = points.geometry.within(india_geometry)

    result = points.loc[inside].copy()

    return result.drop(columns=["geometry"])


def parse_detection_time(row) -> datetime:
    """Convert FIRMS date/time fields into UTC datetime."""

    acq_time = int(float(row["acq_time"]))
    hhmm = f"{acq_time:04d}"

    return pd.to_datetime(
        f"{row['acq_date']} {hhmm}",
        format="%Y-%m-%d %H%M",
        utc=True,
    ).to_pydatetime()


def map_confidence(value) -> float:
    """Convert FIRMS confidence letters to NETRIXA confidence."""

    confidence = str(value).strip().lower()

    mapping = {
        "l": 40.0,
        "n": 70.0,
        "h": 90.0,
    }

    if confidence in mapping:
        return mapping[confidence]

    return float(confidence)


def event_exists(
    db,
    latitude: float,
    longitude: float,
    detection_time: datetime,
    satellite: str,
) -> bool:
    """
    Check whether this FIRMS detection is already stored.

    A small coordinate tolerance is used because the same detection
    should have the same satellite/time/location combination.
    """

    stmt = select(ThermalEvent.event_id).where(
        ThermalEvent.satellite == satellite,
        ThermalEvent.detection_time == detection_time,
        ThermalEvent.latitude.between(
            latitude - 0.00001,
            latitude + 0.00001,
        ),
        ThermalEvent.longitude.between(
            longitude - 0.00001,
            longitude + 0.00001,
        ),
    )

    return db.execute(stmt).first() is not None


def next_event_id(db) -> str:
    """Generate the next NTX-FIRMS event ID."""

    events = db.execute(
        select(ThermalEvent.event_id)
        .where(ThermalEvent.event_id.like("NTX-FIRMS-%"))
    ).scalars().all()

    max_number = 0

    for event_id in events:
        try:
            number = int(event_id.split("-")[-1])
            max_number = max(max_number, number)
        except ValueError:
            continue

    return f"NTX-FIRMS-{max_number + 1:06d}"


def ingest_dataframe(df: pd.DataFrame, db) -> int:
    """Insert new FIRMS detections and run the NETRIXA pipeline."""

    inserted = 0

    for _, row in df.iterrows():
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])

        detection_time = parse_detection_time(row)

        satellite = str(row["satellite"])
        instrument = str(row["instrument"])

        if event_exists(
            db,
            latitude,
            longitude,
            detection_time,
            satellite,
        ):
            continue

        confidence = map_confidence(row["confidence"])

        event_id = next_event_id(db)

        event = ThermalEvent(
            event_id=event_id,
            latitude=latitude,
            longitude=longitude,
            geom=f"SRID=4326;POINT({longitude} {latitude})",
            detection_time=detection_time,
            brightness_temperature=float(row["bright_ti4"]),
            frp=float(row["frp"]),
            confidence=confidence,
            satellite=satellite,
            instrument=instrument,
            source="FIRMS",
        )

        db.add(event)
        db.flush()

        # Run geospatial + temporal + classification + risk analysis.
        process_event(db, event)

        inserted += 1

    return inserted


def sync_once() -> dict:
    """Perform one complete FIRMS synchronization."""

    settings = get_settings()

    if not settings.FIRMS_API_KEY:
        raise RuntimeError(
            "FIRMS_API_KEY is not configured in backend/.env"
        )

    india_geometry = load_india_boundary()

    frames = []

    for source in SOURCES:
        try:
            df = fetch_source(
                source,
                settings.FIRMS_API_KEY,
            )

            if not df.empty:
                frames.append(df)

        except requests.RequestException as exc:
            print(f"FIRMS error ({source}): {exc}")

    if not frames:
        return {
            "fetched": 0,
            "india": 0,
            "inserted": 0,
        }

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    india_df = filter_india(
        combined,
        india_geometry,
    )

    with session_scope() as db:
        inserted = ingest_dataframe(
            india_df,
            db,
        )

    result = {
        "fetched": len(combined),
        "india": len(india_df),
        "inserted": inserted,
    }

    print(
        "FIRMS sync:",
        result,
    )


    return result
async def live_firms_loop():
    """Continuously synchronize NASA FIRMS every 10 minutes."""

    print("=" * 60)
    print("NETRIXA LIVE FIRMS TRACKER STARTED")
    print("Sync interval: 10 minutes")
    print("=" * 60)

    while True:
        try:
            await asyncio.to_thread(sync_once)

        except Exception as exc:
            print(f"FIRMS live sync failed: {exc}")

        await asyncio.sleep(SYNC_INTERVAL_SECONDS)