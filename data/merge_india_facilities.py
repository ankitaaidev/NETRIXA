from pathlib import Path
import geopandas as gpd
import pandas as pd


BASE_DIR = Path(r"C:\NETRIXA")

INPUTS = {
    "eastern": BASE_DIR / "data/raw/osm/india_facilities/eastern_facilities_fixed.geojson",
    "central": BASE_DIR / "data/raw/osm/india_facilities/central_facilities.geojson",
    "north_eastern": BASE_DIR / "data/raw/osm/india_facilities/north_eastern_facilities.geojson",
    "northern": BASE_DIR / "data/raw/osm/india_facilities/northern_facilities.geojson",
    "southern": BASE_DIR / "data/raw/osm/india_facilities/southern_facilities.geojson",
    "western": BASE_DIR / "data/raw/osm/india_facilities/western_facilities.geojson",
}

OUTPUT = BASE_DIR / "data/raw/osm/india_facilities/india_facilities.geojson"


def main():
    print("=" * 70)
    print("MERGING INDIA-WIDE OSM FACILITIES")
    print("=" * 70)

    frames = []

    for region, path in INPUTS.items():
        print()
        print(f"Loading: {region.upper()}")
        print(path)

        if not path.exists():
            raise FileNotFoundError(f"Missing input: {path}")

        gdf = gpd.read_file(path)

        print(f"Features: {len(gdf)}")

        gdf["source_region"] = region

        frames.append(gdf)

    print()
    print("=" * 70)
    print("COMBINING DATASETS")
    print("=" * 70)

    combined = gpd.GeoDataFrame(
        pd.concat(frames, ignore_index=True),
        crs=frames[0].crs,
    )

    print(f"Features before deduplication: {len(combined)}")

    # Remove exact duplicate OSM objects when the same OSM identifier
    # appears more than once across regional extracts.
    if "osm_id" in combined.columns:
        before = len(combined)

        combined = combined.drop_duplicates(
            subset=["osm_type", "osm_id"],
            keep="first",
        )

        removed = before - len(combined)

        print(f"Duplicate OSM objects removed: {removed}")

    print()
    print("=" * 70)
    print("FINAL QUALITY CHECK")
    print("=" * 70)

    print(f"Final features: {len(combined)}")
    print(f"Invalid geometries: {(~combined.geometry.is_valid).sum()}")
    print(f"Empty geometries: {combined.geometry.is_empty.sum()}")

    print()
    print("Geometry types:")
    print(combined.geometry.geom_type.value_counts())

    print()
    print("NETRIXA roles:")
    print(combined["osm_role"].value_counts(dropna=False))

    print()
    print("Source regions:")
    print(combined["source_region"].value_counts())

    print()
    print("Writing:")
    print(OUTPUT)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    combined.to_file(
        OUTPUT,
        driver="GeoJSON",
    )

    print()
    print("=" * 70)
    print("MERGE COMPLETE")
    print("=" * 70)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()