import os

import osmnx as ox


OUTPUT_FILE = "data/raw/boundaries/india.geojson"


def main():
    print("=" * 60)
    print("NETRIXA - CREATE INDIA BOUNDARY")
    print("=" * 60)

    print("Downloading India boundary from OpenStreetMap...")

    # Use the working Overpass server discovered during the OSM testing.
    ox.settings.overpass_url = "https://overpass.private.coffee/api"

    india = ox.geocode_to_gdf("India")

    if india.empty:
        raise RuntimeError("India boundary could not be loaded.")

    india = india.to_crs("EPSG:4326")

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True,
    )

    india.to_file(
        OUTPUT_FILE,
        driver="GeoJSON",
    )

    print()
    print("=" * 60)
    print("BOUNDARY CREATED")
    print("=" * 60)
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Features: {len(india)}")
    print(f"CRS: {india.crs}")
    print("=" * 60)


if __name__ == "__main__":
    main()