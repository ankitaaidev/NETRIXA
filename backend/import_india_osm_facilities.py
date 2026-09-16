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
    / "india_facilities"
    / "india_facilities.geojson"
)


def map_category(row) -> FacilityCategory:
    facility_type = str(row.get("facility_type") or "").lower()
    industrial = str(row.get("osm_industrial") or "").lower()
    power = str(row.get("osm_power") or "").lower()
    man_made = str(row.get("osm_man_made") or "").lower()

    text = f"{facility_type} {industrial} {power} {man_made}"

    if "refinery" in text or "oil" in text:
        return FacilityCategory.REFINERY

    if "petrochemical" in text:
        return FacilityCategory.PETROCHEMICAL

    if "steel" in text:
        return FacilityCategory.STEEL

    if "mine" in text or "mining" in text or "quarry" in text:
        return FacilityCategory.MINING

    if power in {"plant", "generator"} or "power plant" in facility_type:
        return FacilityCategory.THERMAL_POWER

    if "lng" in text:
        return FacilityCategory.LNG

    return FacilityCategory.OTHER


def get_facility_type(row) -> str:
    value = str(row.get("facility_type") or "").strip()

    if value:
        return value

    return "Industrial Facility"


def get_name(row, osm_type: str, osm_id: int) -> str:
    name = str(row.get("name") or "").strip()

    if name:
        return name

    return f"OSM {osm_type} {osm_id}"


def main() -> None:
    if not OSM_PATH.exists():
        raise FileNotFoundError(f"India-wide OSM file not found: {OSM_PATH}")

    print(f"Reading: {OSM_PATH}")

    gdf = gpd.read_file(OSM_PATH)

    if gdf.empty:
        raise ValueError("India-wide OSM GeoJSON contains no features.")

    if gdf.crs is None:
        raise ValueError("India-wide OSM GeoJSON has no CRS.")

    print(f"Total GeoJSON features: {len(gdf)}")

    # Only FACILITY and COMPONENT records belong in the facilities table.
    allowed_roles = {"FACILITY", "COMPONENT"}
    gdf = gdf[
        gdf["osm_role"].astype(str).str.upper().isin(allowed_roles)
    ].copy()

    print(f"FACILITY + COMPONENT features: {len(gdf)}")

    # Convert every geometry to a representative point.
    projected = gdf.to_crs("EPSG:3857")
    projected["representative_point"] = projected.geometry.representative_point()

    representative = projected.set_geometry(
        "representative_point"
    ).to_crs("EPSG:4326")

    imported = 0
    skipped = 0

    with session_scope() as db:
        for _, row in representative.iterrows():
            osm_type = str(row.get("osm_type") or "").strip().lower()
            osm_id = row.get("osm_id")

            if not osm_type or osm_id is None:
                skipped += 1
                continue

            facility_id = f"OSM-{osm_type.upper()}-{int(osm_id)}"

            existing = db.scalar(
                select(Facility).where(
                    Facility.facility_id == facility_id
                )
            )

            if existing:
                skipped += 1
                continue

            point = row["representative_point"]

            if point is None or point.is_empty:
                skipped += 1
                continue

            name = get_name(row, osm_type, int(osm_id))

            facility = Facility(
                facility_id=facility_id,
                name=name,
                facility_type=get_facility_type(row),
                facility_category=map_category(row),
                latitude=float(point.y),
                longitude=float(point.x),
                geom=f"SRID=4326;POINT({point.x} {point.y})",
                state="Unknown",
                district="Unknown",
                source="OSM",
            )

            db.add(facility)
            imported += 1

            if imported % 1000 == 0:
                print(f"Prepared {imported} facilities...")

        print()
        print(f"Imported: {imported}")
        print(f"Skipped: {skipped}")
        print(f"Final input features: {len(gdf)}")


if __name__ == "__main__":
    main()