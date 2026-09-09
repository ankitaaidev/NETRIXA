import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests


MAP_KEY = os.getenv("FIRMS_MAP_KEY")

if not MAP_KEY:
    raise RuntimeError("FIRMS_MAP_KEY is not set")


# --------------------------------------------------
# Configuration
# --------------------------------------------------

WEST = 68
SOUTH = 6
EAST = 98
NORTH = 36

START_DATE = date(2026, 8, 1)
END_DATE = date(2026, 9, 6)

DAYS_PER_REQUEST = 5

OUTPUT_DIR = Path("data/raw/firms/history")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


SOURCES = {
    "VIIRS_NOAA20_NRT": "noaa20",
    "VIIRS_NOAA21_NRT": "noaa21",
}


# --------------------------------------------------
# Download
# --------------------------------------------------

def download_window(source, source_name, start_date):

    end_date = min(
        start_date + timedelta(days=DAYS_PER_REQUEST - 1),
        END_DATE,
    )

    days = (end_date - start_date).days + 1

    url = (
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{MAP_KEY}/{source}/"
        f"{WEST},{SOUTH},{EAST},{NORTH}/"
        f"{days}/{start_date.isoformat()}"
    )

    print()
    print("=" * 70)
    print(f"Source : {source}")
    print(f"Dates  : {start_date} → {end_date}")
    print(f"Days   : {days}")
    print("=" * 70)

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    output_file = (
        OUTPUT_DIR
        / f"{source_name}_{start_date}_{end_date}.csv"
    )

    output_file.write_bytes(response.content)

    df = pd.read_csv(output_file)

    print(f"Downloaded events: {len(df)}")
    print(f"Saved: {output_file}")

    return output_file


def main():

    current_date = START_DATE

    all_files = []

    while current_date <= END_DATE:

        for source, source_name in SOURCES.items():

            output_file = download_window(
                source,
                source_name,
                current_date,
            )

            all_files.append(output_file)

        current_date += timedelta(days=DAYS_PER_REQUEST)

    print()
    print("=" * 70)
    print("Historical FIRMS download completed.")
    print(f"Files downloaded: {len(all_files)}")
    print("=" * 70)


if __name__ == "__main__":
    main()