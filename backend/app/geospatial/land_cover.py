"""
Real land-cover lookup using ESA WorldCover 2021 v200.

WorldCover tiles are 3° x 3° GeoTIFFs in EPSG:4326 at approximately
10 m resolution.

The raster provides the actual land-cover observation. Industrial
classification is NOT inferred from the WorldCover "Built-up" class alone.
A nearby industrial facility is used as additional evidence.
"""

from pathlib import Path
from math import floor

import rasterio

from app.geospatial.regions import STATE_BOUNDS


# C:\NETRIXA\data\raw\land_cover\worldcover_2021
PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORLD_COVER_DIR = (
    PROJECT_ROOT / "data" / "raw" / "land_cover" / "worldcover_2021"
)


# ESA WorldCover 2021 class codes.
WORLDCOVER_CLASSES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare/sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}


def _tile_name(latitude: float, longitude: float) -> str:
    """
    Return the ESA WorldCover 3° x 3° tile containing the point.

    Example:
        latitude=22.5, longitude=88.3
        -> N21E087
    """

    lat_origin = floor(latitude / 3) * 3
    lon_origin = floor(longitude / 3) * 3

    if lat_origin >= 0:
        lat_part = f"N{lat_origin:02d}"
    else:
        lat_part = f"S{abs(lat_origin):02d}"

    if lon_origin >= 0:
        lon_part = f"E{lon_origin:03d}"
    else:
        lon_part = f"W{abs(lon_origin):03d}"

    return f"{lat_part}{lon_part}"


def _tile_path(latitude: float, longitude: float) -> Path:
    tile = _tile_name(latitude, longitude)

    return WORLD_COVER_DIR / (
        f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    )


def _worldcover_class(
    latitude: float,
    longitude: float,
) -> tuple[int | None, str | None]:
    """
    Read the WorldCover class at one latitude/longitude.

    Returns:
        (class_code, class_name)

    Returns (None, None) when the required tile is unavailable or the
    coordinate cannot be read.
    """

    path = _tile_path(latitude, longitude)

    if not path.exists():
        return None, None

    try:
        with rasterio.open(path) as src:
            value = next(src.sample([(longitude, latitude)]))[0]

            if src.nodata is not None and value == src.nodata:
                return None, None

            class_code = int(value)
            class_name = WORLDCOVER_CLASSES.get(
                class_code,
                "Unknown",
            )

            return class_code, class_name

    except Exception:
        return None, None


def reverse_geocode_state(
    latitude: float,
    longitude: float,
) -> str | None:
    """
    Rough state lookup using the existing reference bounding boxes.
    """

    for state, (
        lat_min,
        lat_max,
        lon_min,
        lon_max,
    ) in STATE_BOUNDS.items():

        if (
            lat_min <= latitude <= lat_max
            and lon_min <= longitude <= lon_max
        ):
            return state

    return None


def _map_worldcover_to_classifier(
    class_code: int,
    class_name: str,
    nearest_facility_distance_m: float | None,
) -> str:
    """
    Convert ESA WorldCover into NETRIXA's land-cover vocabulary.

    Built-up remains "Built-up" because WorldCover does not distinguish
    industrial from residential/commercial built-up land. Industrial
    context is determined separately using OSM facility proximity.
    """

    if class_code == 10:
        return "Forest"

    if class_code == 40:
        return "Cropland"

    if class_code == 50:
        return "Built-up"

    if class_code == 60:
        return "Barren/Mining"

    if class_code == 95:
        return "Forest"

    return "Mixed/Unclassified"
    """
    Convert the real ESA WorldCover class into the existing NETRIXA
    classifier's land-cover vocabulary.

    WorldCover itself does not have an "Industrial" class. Built-up
    land is therefore considered Industrial only when a known industrial
    facility is also nearby.
    """

    if class_code == 40:
        return "Cropland"

    if class_code in (10, 95):
        return "Forest"

    if class_code == 60:
        return "Barren/Mining"

    if (
        class_code == 50
        and nearest_facility_distance_m is not None
        and nearest_facility_distance_m <= 2000
    ):
        return "Industrial"

    return "Mixed/Unclassified"


def land_cover_context(
    latitude: float,
    longitude: float,
    nearest_facility_distance_m: float | None,
) -> dict:
    """
    Get actual land-cover information from ESA WorldCover.

    The returned land_cover value remains compatible with the existing
    NETRIXA classifier.
    """

    class_code, class_name = _worldcover_class(
        latitude,
        longitude,
    )

    if class_code is None:
        return {
            "land_cover": "Mixed/Unclassified",
            "basis": "ESA WorldCover tile unavailable or unreadable",
        }

    classifier_label = _map_worldcover_to_classifier(
        class_code,
        class_name,
        nearest_facility_distance_m,
    )

    return {
        "land_cover": classifier_label,
        "basis": (
            f"ESA WorldCover 2021 v200, "
            f"class {class_code} ({class_name})"
        ),
    }


def resolve_land_cover(
    known_land_cover: str | None,
    latitude: float,
    longitude: float,
    nearest_facility_distance_m: float | None,
) -> dict:
    """
    Resolve land cover from ESA WorldCover first.

    Previously stored land-cover values are used only when the WorldCover
    tile is unavailable or unreadable.
    """

    class_code, class_name = _worldcover_class(
        latitude,
        longitude,
    )

    if class_code is not None:
        classifier_label = _map_worldcover_to_classifier(
            class_code,
            class_name,
            nearest_facility_distance_m,
        )

        return {
            "land_cover": classifier_label,
            "basis": (
                f"ESA WorldCover 2021 v200, "
                f"class {class_code} ({class_name})"
            ),
        }

    if known_land_cover:
        return {
            "land_cover": known_land_cover,
            "basis": "fallback to previously known source value",
        }

    return {
        "land_cover": "Mixed/Unclassified",
        "basis": "ESA WorldCover tile unavailable or unreadable",
    }