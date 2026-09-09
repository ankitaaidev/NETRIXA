import osmnx as ox
import geopandas as gpd
import pandas as pd

INPUT_FILE = "data/processed/thermal_events.csv"
OUTPUT_FILE = "data/processed/thermal_events_india.csv"

print("Loading FIRMS events...")
firms = pd.read_csv(INPUT_FILE)

print(f"Original FIRMS events: {len(firms)}")

# Convert FIRMS points to GeoDataFrame
firms_gdf = gpd.GeoDataFrame(
    firms,
    geometry=gpd.points_from_xy(
        firms["longitude"],
        firms["latitude"]
    ),
    crs="EPSG:4326"
)

print("Downloading India administrative boundary...")

india = ox.geocode_to_gdf("India")

# Make sure both datasets use the same CRS
india = india.to_crs("EPSG:4326")

print("Filtering FIRMS events to India...")

# Keep only points inside India
filtered = gpd.sjoin(
    firms_gdf,
    india[["geometry"]],
    how="inner",
    predicate="within"
)

# Remove spatial columns
filtered = filtered.drop(
    columns=["geometry", "index_right"],
    errors="ignore"
)

filtered.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("========================================")
print("India FIRMS filtering completed.")
print(f"Original events: {len(firms)}")
print(f"Events inside India: {len(filtered)}")
print(f"Removed: {len(firms) - len(filtered)}")
print(f"Output: {OUTPUT_FILE}")
print("========================================")