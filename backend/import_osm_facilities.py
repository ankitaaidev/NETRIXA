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
    / "kolkata_industrial_facilities.geojson"
)


def map_category(row) -> FacilityCategory:
    industrial = str(row.get("industrial") or "").lower()
    power = str(row.get("power") or "").lower()
    man_made = str(row.get("man_made") or "").lower()

    if "steel" in industrial or "steel" in str(row.get("name") or "").lower():
        return FacilityCategory.STEEL

    if industrial in {"mine", "mining"}:
        return FacilityCategory.MINING

    if power in {"plant", "generator"}:
        return FacilityCategory.THERMAL_POWER

    if industrial in {"oil", "oil_refinery", "refinery"}:
        return FacilityCategory.REFINERY

    if industrial in {"petrochemical"}:
        return FacilityCategory.PETROCHEMICAL

    if man_made in {"storage_tank", "gasometer"}:
        return FacilityCategory.OTHER

    return FacilityCategory.OTHER


def facility_type(row) -> str:
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


def main() -> None:
    if not OSM_PATH.exists():
        raise FileNotFoundError(f"OSM file not found: {OSM_PATH}")

    gdf = gpd.read_file(OSM_PATH)

    if gdf.empty:
        raise ValueError("OSM GeoJSON contains no features.")

    if gdf.crs is None:
        raise ValueError("OSM GeoJSON has no CRS.")

    # Representative points are calculated in a projected CRS
    # and then converted back to WGS84.
    projected = gdf.to_crs("EPSG:3857")
    projected["representative_point"] = projected.geometry.representative_point()
    representative = projected.set_geometry("representative_point").to_crs("EPSG:4326")

    imported = 0
    skipped = 0

    with session_scope() as db:
        for index, row in representative.iterrows():
            facility_id = f"OSM-KOL-{index + 1:04d}"

            existing = db.scalar(
                select(Facility).where(Facility.facility_id == facility_id)
            )

            if existing:
                skipped += 1
                continue

            point = row["representative_point"]

            name = str(row.get("name") or "").strip()
            if not name:
                name = f"OSM Industrial Facility {index + 1}"

            facility = Facility(
            facility_id=facility_id,
            name=name,
            facility_type=facility_type(row),
            facility_category=map_category(row),
            latitude=float(point.y),
            longitude=float(point.x),
            geom=f"SRID=4326;POINT({point.x} {point.y})",
            state="West Bengal",
            district="Kolkata",
            source="OSM",
        )

            db.add(facility)
            imported += 1

        print(f"Imported: {imported}")
        print(f"Skipped existing: {skipped}")
        print(f"Total OSM features: {len(gdf)}")


if __name__ == "__main__":
    main()