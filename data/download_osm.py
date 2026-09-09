import osmnx as ox

OUTPUT = "data/raw/osm/kolkata_industrial_facilities.geojson"

# Small test area around Kolkata
north = 22.80
south = 22.45
east = 88.55
west = 88.15

tags = {
    "industrial": True,
    "power": ["plant", "generator"],
    "man_made": ["works", "oil_well", "gasometer", "storage_tank"],
}

print("Downloading OSM industrial facilities around Kolkata...")

try:
    gdf = ox.features_from_bbox(
        bbox=(west, south, east, north),
        tags=tags,
    )

    print(f"Downloaded {len(gdf)} features.")

    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf.to_crs("EPSG:4326")

    gdf.to_file(
        OUTPUT,
        driver="GeoJSON",
    )

    print(f"Saved: {OUTPUT}")
    print("OSM download completed.")

except Exception as e:
    print(f"OSM download failed: {e}")