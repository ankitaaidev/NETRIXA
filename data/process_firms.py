import pandas as pd

NOAA20 = "data/raw/firms/viirs_noaa20/india_7days.csv"
NOAA21 = "data/raw/firms/viirs_noaa21/india_7days.csv"

OUTPUT = "data/processed/thermal_events.csv"


def load_firms(path):
    df = pd.read_csv(path)

    df["acq_datetime"] = pd.to_datetime(
        df["acq_date"].astype(str)
        + " "
        + df["acq_time"].astype(str).str.zfill(4),
        format="%Y-%m-%d %H%M",
        errors="coerce",
    )

    return df


print("Loading NOAA-20...")
noaa20 = load_firms(NOAA20)

print("Loading NOAA-21...")
noaa21 = load_firms(NOAA21)

print("Combining datasets...")
df = pd.concat([noaa20, noaa21], ignore_index=True)

# Rename FIRMS fields to NETRIXA-friendly names
df = df.rename(
    columns={
        "bright_ti4": "brightness",
        "frp": "frp",
        "confidence": "confidence",
        "satellite": "satellite",
        "daynight": "daynight",
    }
)

# Keep the important fields for NETRIXA
columns = [
    "latitude",
    "longitude",
    "acq_date",
    "acq_time",
    "acq_datetime",
    "brightness",
    "bright_ti5",
    "frp",
    "confidence",
    "satellite",
    "instrument",
    "daynight",
    "scan",
    "track",
    "version",
]

df = df[columns]

# Remove invalid coordinates
df = df.dropna(subset=["latitude", "longitude"])

df = df[
    (df["latitude"].between(6, 36))
    & (df["longitude"].between(68, 98))
]

# Sort chronologically
df = df.sort_values("acq_datetime")

# Save processed dataset
df.to_csv(OUTPUT, index=False)

print()
print("FIRMS processing completed.")
print(f"Total thermal events: {len(df)}")
print(f"Output: {OUTPUT}")
print()
print(df.head())