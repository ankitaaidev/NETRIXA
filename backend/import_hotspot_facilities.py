from pathlib import Path

import geopandas as gpd
from sqlalchemy import select

from app.database.session import session_scope
from app.models.facility import Facility, FacilityCategory


OSM_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "osm"
    / "hotspot_cells"
    / "osm_15.1_76.6.geojson"
)


def map_category(row):
    industrial = str(row.get("industrial") or "").lower()
    power = str(row.get("power") or "").lower()
    man_made = str(row.get("man_made") or "").lower()
    name = str(row.get("name") or "").lower()

    if industrial == "steel_mill" or "steel" in name:
        return FacilityCategory.STEEL

    if industrial in {"mine", "mining"}:
        return FacilityCategory.MINING

    if power in {"plant", "generator"}:
        return FacilityCategory.THERMAL_POWER

    return FacilityCategory.OTHER


def get_facility_type(row):
    industrial = str(row.get("industrial") or "").strip()
    power = str(row.get("power") or "").strip()
    man_made = str(row.get("man_made") or "").strip()

    if industrial:
        return industrial.replace("_", " ").title()

    if power:
        return f"Power {power.title()}"

    if man_made:
        return man_made.replace("_", " ").title()

    return "Industrial Facility"


def main():
    if not OSM_PATH.exists():
        raise FileNotFoundError(OSM_PATH)

    gdf = gpd.read_file(OSM_PATH)

    projected = gdf.to_crs("EPSG:3857")
    projected["representative_point"] = projected.geometry.representative_point()
    points = projected.set_geometry("representative_point").to_crs("EPSG:4326")

    imported = 0
    skipped = 0

    with session_scope() as db:
        for index, row in points.iterrows():
            facility_id = f"OSM-HOT-15-76-{index + 1:03d}"

            existing = db.scalar(
                select(Facility).where(Facility.facility_id == facility_id)
            )

            if existing:
                skipped += 1
                continue

            point = row["representative_point"]

            name = str(row.get("name") or "").strip()
            if not name:
                name = f"OSM Hotspot Facility {index + 1}"

            db.add(
                Facility(
                    facility_id=facility_id,
                    name=name,
                    facility_type=get_facility_type(row),
                    facility_category=map_category(row),
                    latitude=float(point.y),
                    longitude=float(point.x),
                    geom=f"SRID=4326;POINT({point.x} {point.y})",
                    state="Karnataka",
                    district="Vijayanagara",
                    source="OSM",
                )
            )

            imported += 1

    print(f"Imported: {imported}")
    print(f"Skipped existing: {skipped}")
    print(f"Total OSM features: {len(gdf)}")


if __name__ == "__main__":
    main()