import pandas as pd
import geopandas as gpd
from shapely.geometry import box

FIRMS_FILE = "data/processed/thermal_events_india.csv"
OUTPUT_FILE = "data/processed/osm_microgrid.geojson"

GRID_SIZE = 0.1

print("Loading India FIRMS events...")

df = pd.read_csv(FIRMS_FILE)

# Create 0.1° × 0.1° cells
df["grid_lat"] = (df["latitude"] // GRID_SIZE) * GRID_SIZE
df["grid_lon"] = (df["longitude"] // GRID_SIZE) * GRID_SIZE

# Count thermal events
grid_counts = (
    df.groupby(["grid_lat", "grid_lon"])
    .size()
    .reset_index(name="event_count")
)

# Create polygons
geometry = [
    box(
        lon,
        lat,
        lon + GRID_SIZE,
        lat + GRID_SIZE
    )
    for lat, lon in zip(
        grid_counts["grid_lat"],
        grid_counts["grid_lon"]
    )
]

grid = gpd.GeoDataFrame(
    grid_counts,
    geometry=geometry,
    crs="EPSG:4326"
)

grid = grid.sort_values(
    "event_count",
    ascending=False
)

grid.to_file(
    OUTPUT_FILE,
    driver="GeoJSON"
)

print()
print("========================================")
print("OSM micro-grid created.")
print(f"Total micro-cells: {len(grid)}")
print()
print("Top 30 micro-cells:")
print(
    grid[
        ["grid_lat", "grid_lon", "event_count"]
    ].head(30).to_string(index=False)
)
print()
print(f"Saved: {OUTPUT_FILE}")
print("========================================")