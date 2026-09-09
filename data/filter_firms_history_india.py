import pandas as pd
import geopandas as gpd
import osmnx as ox

INPUT_FILE = "data/processed/firms_history_india.csv"
OUTPUT_FILE = "data/processed/firms_history_india_clean.csv"

print("Loading historical FIRMS data...")

df = pd.read_csv(INPUT_FILE)

print(f"Input rows: {len(df)}")

# --------------------------------------------------
# Convert FIRMS points into GeoDataFrame
# --------------------------------------------------

gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["longitude"],
        df["latitude"]
    ),
    crs="EPSG:4326"
)

# --------------------------------------------------
# Get actual India boundary
# --------------------------------------------------

print("Loading India boundary from OSM...")

india = ox.geocode_to_gdf("India")

india = india.to_crs("EPSG:4326")

india_geometry = india.geometry.union_all()

# --------------------------------------------------
# Spatial filtering
# --------------------------------------------------

print("Applying India boundary...")

inside = gdf.geometry.within(india_geometry)

gdf_india = gdf[inside].copy()

print(f"Inside India: {len(gdf_india)}")
print(f"Removed: {len(gdf) - len(gdf_india)}")

# --------------------------------------------------
# Remove geometry before CSV
# --------------------------------------------------

gdf_india = pd.DataFrame(gdf_india.drop(columns="geometry"))

# --------------------------------------------------
# Save
# --------------------------------------------------

gdf_india.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 70)
print("India historical FIRMS filtering completed.")
print("=" * 70)

print(f"Final rows: {len(gdf_india)}")
print(f"Date range: {gdf_india['acq_date'].min()} → {gdf_india['acq_date'].max()}")
print(f"Output: {OUTPUT_FILE}")