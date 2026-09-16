import io
import os
from datetime import datetime, timezone

import pandas as pd
import requests


FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY")

if not FIRMS_MAP_KEY:
    raise RuntimeError("FIRMS_MAP_KEY is not set.")

WEST = 68
SOUTH = 6
EAST = 98
NORTH = 36

SOURCES = [
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT",
]

BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def fetch_source(source: str) -> pd.DataFrame:
    url = (
        f"{BASE_URL}/{FIRMS_MAP_KEY}/"
        f"{source}/{WEST},{SOUTH},{EAST},{NORTH}/1"
    )

    print(f"Fetching {source}...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    if not response.text.strip():
        print(f"No data returned for {source}.")
        return pd.DataFrame()

    df = pd.read_csv(io.StringIO(response.text))

    print(f"{source}: {len(df)} detections")

    return df


def main():
    print("=" * 60)
    print("NETRIXA LIVE FIRMS FETCH")
    print("=" * 60)

    print(
        "UTC:",
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )

    frames = []

    for source in SOURCES:
        try:
            df = fetch_source(source)

            if not df.empty:
                frames.append(df)

        except requests.RequestException as exc:
            print(f"ERROR fetching {source}: {exc}")

    if not frames:
        print("No FIRMS data received.")
        return

    combined = pd.concat(frames, ignore_index=True)

    print()
    print("=" * 60)
    print("LIVE FIRMS RESULT")
    print("=" * 60)

    print(f"Total detections: {len(combined)}")

    if "satellite" in combined.columns:
        print()
        print("By satellite:")
        print(combined["satellite"].value_counts())

    if "acq_date" in combined.columns:
        print()
        print("Detection dates:")
        print(
            combined["acq_date"].min(),
            "to",
            combined["acq_date"].max(),
        )

    print()
    print("Columns:")
    print(list(combined.columns))

    # Save the live FIRMS data
    os.makedirs("data/raw/firms", exist_ok=True)

    output_file = "data/raw/firms/live_firms.csv"

    combined.to_csv(
        output_file,
        index=False,
    )

    print()
    print("Saved live data:")
    print(output_file)


if __name__ == "__main__":
    main()