from pathlib import Path

import pandas as pd


INPUT_DIR = Path("data/raw/firms/history")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "firms_history_india.csv"


def main():

    files = sorted(INPUT_DIR.glob("*.csv"))

    if not files:
        raise RuntimeError("No historical FIRMS CSV files found.")

    print(f"Found {len(files)} historical files.")

    frames = []

    for file in files:
        print(f"Reading: {file}")

        df = pd.read_csv(file)

        if df.empty:
            print("  Empty file - skipped")
            continue

        df["source_file"] = file.name

        frames.append(df)

    if not frames:
        raise RuntimeError("No FIRMS data found.")

    df = pd.concat(frames, ignore_index=True)

    print()
    print(f"Raw rows: {len(df)}")

    # --------------------------------------------------
    # Standardize column names
    # --------------------------------------------------

    df.columns = [column.strip().lower() for column in df.columns]

    # --------------------------------------------------
    # Create datetime
    # --------------------------------------------------

    df["acq_date"] = pd.to_datetime(
        df["acq_date"],
        errors="coerce"
    )

    df["acq_datetime"] = pd.to_datetime(
        df["acq_date"].dt.strftime("%Y-%m-%d")
        + " "
        + df["acq_time"].astype(str).str.zfill(4),
        format="%Y-%m-%d %H%M",
        errors="coerce"
    )

    # --------------------------------------------------
    # Remove invalid coordinates
    # --------------------------------------------------

    before = len(df)

    df = df[
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
    ].copy()

    print(f"Removed invalid coordinates: {before - len(df)}")

    # --------------------------------------------------
    # India geographic bounding box
    #
    # This is only a first filter.
    # We will apply the proper India boundary next.
    # --------------------------------------------------

    before = len(df)

    df = df[
        df["latitude"].between(6, 36)
        & df["longitude"].between(68, 98)
    ].copy()

    print(f"Inside India bounding box: {len(df)}")
    print(f"Removed by bbox: {before - len(df)}")

    # --------------------------------------------------
    # Remove exact duplicate observations
    # --------------------------------------------------

    before = len(df)

    duplicate_columns = [
        "latitude",
        "longitude",
        "acq_datetime",
        "satellite",
    ]

    df = df.drop_duplicates(
        subset=duplicate_columns
    ).copy()

    print(f"Exact duplicates removed: {before - len(df)}")

    # --------------------------------------------------
    # Sort
    # --------------------------------------------------

    df = df.sort_values(
        ["acq_datetime", "latitude", "longitude"]
    ).reset_index(drop=True)

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("Historical FIRMS processing completed.")
    print("=" * 70)

    print(f"Final rows: {len(df)}")
    print(f"Date range: {df['acq_date'].min()} → {df['acq_date'].max()}")
    print(f"Output: {OUTPUT_FILE}")

    print()
    print("Satellite counts:")
    print(df["satellite"].value_counts())

    print()
    print("Daily counts:")
    print(df["acq_date"].value_counts().sort_index())


if __name__ == "__main__":
    main()