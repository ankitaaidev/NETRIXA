import osmnx as ox

LAT = 15.1
LON = 76.6
GRID_SIZE = 0.1

north = LAT + GRID_SIZE
south = LAT
east = LON + GRID_SIZE
west = LON

tags = {
    "industrial": True,
    "power": ["plant", "generator"],
    "man_made": ["works", "oil_well", "gasometer", "storage_tank"],
}

ox.settings.overpass_url = "https://overpass-api.de/api"
ox.settings.requests_timeout = 60
ox.settings.requests_retries = 2

print("Testing OSM query...")
print(f"Cell: {LAT}, {LON}")
print(f"BBox: {west}, {south}, {east}, {north}")

gdf = ox.features_from_bbox(
    bbox=(west, south, east, north),
    tags=tags,
)

print("\nOSM query successful.")
print(f"Features found: {len(gdf)}")

if not gdf.empty:
    print("\nFeature types:")
    print(
        gdf[["industrial", "power", "man_made"]]
        .stack()
        .value_counts()
        .head(20)
    )

output_dir = r"C:\NETRIXA\data\raw\osm\hotspot_cells"
output_file = rf"{output_dir}\osm_15.1_76.6.geojson"

import os

os.makedirs(output_dir, exist_ok=True)
gdf.to_file(output_file, driver="GeoJSON")

print(f"\nSaved: {output_file}")