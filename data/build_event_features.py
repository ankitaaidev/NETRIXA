import geopandas as gpd
import pandas as pd

FIRMS_FILE = "data/processed/thermal_events.csv"
OSM_FILE = "data/raw/osm/india_facilities/india_facilities.geojson"
OUTPUT_FILE = "data/processed/event_features.csv"

print("Loading FIRMS data...")
firms = pd.read_csv(FIRMS_FILE)

print("Loading OSM facilities...")
osm = gpd.read_file(OSM_FILE)

# Convert FIRMS events to GeoDataFrame
firms_gdf = gpd.GeoDataFrame(
    firms,
    geometry=gpd.points_from_xy(
        firms["longitude"],
        firms["latitude"]
    ),
    crs="EPSG:4326"
)

# Keep useful OSM information
# Keep useful OSM information
# Keep useful OSM information
osm["facility_name"] = osm["name"].fillna("Unnamed facility")

osm = osm[
    [
        "osm_id",
        "osm_role",
        "facility_name",
        "facility_type",
        "osm_power",
        "osm_man_made",
        "osm_industrial",
        "geometry",
    ]
].copy()

# Rename columns to simple names for feature engineering
osm = osm.rename(columns={
    "osm_id": "facility_id",
    "osm_role": "role",
    "osm_power": "power",
    "osm_man_made": "man_made",
    "osm_industrial": "industrial",
})

# Project both datasets to a metric CRS.
# EPSG:3857 gives distances in meters.
firms_projected = firms_gdf.to_crs("EPSG:3857")
osm_projected = osm.to_crs("EPSG:3857")

print("Finding nearest OSM facility for every FIRMS event...")

nearest = gpd.sjoin_nearest(
    firms_projected,
    osm_projected,
    how="left",
    distance_col="distance_meters"
)

# Convert distance to kilometers
nearest["distance_to_industry_km"] = (
    nearest["distance_meters"] / 1000
).round(3)

# Rename OSM ID
nearest = nearest.rename(columns={
    "id": "facility_id"
})

# Remove geometry columns before saving CSV
nearest = nearest.drop(columns=["geometry"], errors="ignore")

# Keep useful ML features
feature_columns = [
    "event_id",
    "latitude",
    "longitude",
    "acq_datetime",
    "frp",
    "confidence",
    "brightness",
    "satellite",
    "instrument",
    "daynight",
    "facility_id",
    "facility_name",
    "facility_type",
    "role",
    "power",
    "man_made",
    "industrial",
    "distance_to_industry_km",
]

# Keep only columns that actually exist
feature_columns = [
    col for col in feature_columns
    if col in nearest.columns
]

features = nearest[feature_columns]

features.to_csv(OUTPUT_FILE, index=False)

print()
print("Feature engineering completed.")
print(f"FIRMS events processed: {len(features)}")
print(f"Output: {OUTPUT_FILE}")
print()
print(features.head())