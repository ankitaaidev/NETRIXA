import os
import time
import pandas as pd
import geopandas as gpd
import osmnx as ox

GRID_FILE = "data/processed/osm_microgrid.geojson"
OUTPUT_FILE = "data/raw/osm/industrial_facilities_india_top20.geojson"

TOP_N = 20

# Working Overpass server
ox.settings.overpass_url = "https://overpass.private.coffee/api/interpreter"

# Don't let OSMnx repeatedly retry a failed request for too long
ox.settings.requests_timeout = 60

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

print("Loading FIRMS hotspot micro-grid...")

grid = gpd.read_file(GRID_FILE)

top_cells = (
    grid.sort_values("event_count", ascending=False)
    .head(TOP_N)
)

print(f"Selected top {len(top_cells)} micro-cells.")
print()

all_features = []

for number, (_, row) in enumerate(top_cells.iterrows(), start=1):

    lat = float(row["grid_lat"])
    lon = float(row["grid_lon"])
    event_count = int(row["event_count"])

    south = lat
    north = lat + 0.1
    west = lon
    east = lon + 0.1

    print(
        f"[{number}/{len(top_cells)}] "
        f"Cell ({lat}, {lon}) | "
        f"FIRMS events: {event_count}"
    )

    try:
        gdf = ox.features_from_bbox(
            bbox=(west, south, east, north),
            tags=tags,
        )

        print(f"    OSM features found: {len(gdf)}")

        if len(gdf) > 0:
            gdf = gdf.copy()

            gdf["firms_grid_lat"] = lat
            gdf["firms_grid_lon"] = lon
            gdf["firms_event_count"] = event_count

            all_features.append(gdf)

    except Exception as e:
        print(f"    FAILED: {type(e).__name__}: {e}")

    # Pause between requests
    time.sleep(3)

print()
print("Combining OSM features...")

if not all_features:
    raise RuntimeError(
        "No OSM features were downloaded."
    )

combined = gpd.GeoDataFrame(
    pd.concat(all_features, ignore_index=True),
    crs="EPSG:4326",
)

before = len(combined)

# Remove exact duplicate geometries
combined = combined.drop_duplicates(
    subset=["geometry"]
)

after = len(combined)

print(f"Features before deduplication: {before}")
print(f"Features after deduplication:  {after}")

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True,
)

combined.to_file(
    OUTPUT_FILE,
    driver="GeoJSON",
)

print()
print("========================================")
print("OSM India hotspot download completed.")
print(f"Unique OSM facilities: {len(combined)}")
print(f"Output: {OUTPUT_FILE}")
print("========================================")