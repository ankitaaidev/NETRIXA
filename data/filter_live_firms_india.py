import os

import geopandas as gpd
import pandas as pd
import osmnx as ox

INPUT_FILE = "data/raw/firms/live_firms.csv"
OUTPUT_FILE = "data/processed/live_firms_india.csv"


def main():
    print("=" * 60)
    print("NETRIXA LIVE FIRMS - INDIA FILTER")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)

    print(f"Input detections: {len(df)}")

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["longitude"],
            df["latitude"],
        ),
        crs="EPSG:4326",
    )

    print("Loading India boundary using OSMnx...")

    india = ox.geocode_to_gdf("India")

    india = india.to_crs("EPSG:4326")

    india_geometry = india.geometry.union_all()

    inside = points.geometry.within(india_geometry)

    india_points = points[inside].copy()

    india_points = india_points.drop(columns=["geometry"])

    os.makedirs("data/processed", exist_ok=True)

    india_points.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 60)
    print("FILTER RESULT")
    print("=" * 60)
    print(f"Input:          {len(df)}")
    print(f"India:          {len(india_points)}")
    print(f"Outside India:  {len(df) - len(india_points)}")
    print()
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()