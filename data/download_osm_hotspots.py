import os
import time
import geopandas as gpd
import osmnx as ox
import pandas as pd

GRID_FILE = "data/processed/osm_hotspot_grid.geojson"
OUTPUT_DIR = "data/raw/osm/hotspot_cells"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Use the working Overpass server
ox.settings.overpass_url = "https://overpass.private.coffee/api/interpreter"

# Load hotspot grid
grid = gpd.read_file(GRID_FILE)

# Take top 10 FIRMS-active cells
top_cells = grid.sort_values(
    "event_count",
    ascending=False
).head(10)

tags = {
    "industrial": True,
    "power": ["plant", "generator"],
    "man_made": [
        "works",
        "oil_well",
        "gasometer",
        "storage_tank",
    ],
}

print(f"Downloading OSM data for {len(top_cells)} hotspot cells...")
print()

all_features = []

for index, row in top_cells.iterrows():

    lat = row["grid_lat"]
    lon = row["grid_lon"]
    count = row["event_count"]

    # One grid cell = 1 degree × 1 degree.
    # Query a smaller central area (0.5° × 0.5°)
    # to avoid very large Overpass requests.
    center_lat = lat + 0.5
    center_lon = lon + 0.5

    half_size = 0.25

    north = center_lat + half_size
    south = center_lat - half_size
    east = center_lon + half_size
    west = center_lon - half_size

    print(
        f"Cell ({lat}, {lon}) | "
        f"FIRMS events: {count}"
    )

    try:
        gdf = ox.features_from_bbox(
            bbox=(west, south, east, north),
            tags=tags,
        )

        print(f"  OSM features: {len(gdf)}")

        if len(gdf) > 0:
            gdf = gdf.copy()
            gdf["source_grid_lat"] = lat
            gdf["source_grid_lon"] = lon
            gdf["firms_event_count"] = count

            all_features.append(gdf)

        # Give the server a little breathing room
        time.sleep(2)

    except Exception as e:
        print(f"  Failed: {e}")

    print()

# Combine all successful cells
if not all_features:
    raise RuntimeError("No OSM features were downloaded.")

combined = gpd.GeoDataFrame(
    pd.concat(all_features, ignore_index=True),
    crs="EPSG:4326",
)

# Remove exact duplicate geometries
combined = combined.drop_duplicates(
    subset=["geometry"]
)

output = os.path.join(
    OUTPUT_DIR,
    "industrial_facilities_top10.geojson"
)

combined.to_file(
    output,
    driver="GeoJSON",
)

print("========================================")
print("OSM hotspot download completed.")
print(f"Total unique OSM features: {len(combined)}")
print(f"Output: {output}")
print("========================================")