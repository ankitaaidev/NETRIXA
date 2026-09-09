import pandas as pd
import geopandas as gpd
from shapely.geometry import box

FIRMS_FILE = "data/processed/thermal_events_india.csv"
OUTPUT_FILE = "data/processed/osm_hotspot_grid.geojson"

# Load FIRMS events
df = pd.read_csv(FIRMS_FILE)

# 1-degree grid
GRID_SIZE = 1.0

df["grid_lat"] = (df["latitude"] // GRID_SIZE) * GRID_SIZE
df["grid_lon"] = (df["longitude"] // GRID_SIZE) * GRID_SIZE

# Count FIRMS events in every grid cell
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

# Sort by thermal activity
grid = grid.sort_values(
    "event_count",
    ascending=False
)

grid.to_file(
    OUTPUT_FILE,
    driver="GeoJSON"
)

print("FIRMS hotspot grid created.")
print(f"Total grid cells with FIRMS events: {len(grid)}")
print()
print("Top 30 cells:")
print(
    grid[
        ["grid_lat", "grid_lon", "event_count"]
    ].head(30).to_string(index=False)
)

print()
print(f"Saved: {OUTPUT_FILE}")