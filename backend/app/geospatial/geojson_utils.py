"""
Minimal GeoJSON helpers. Kept dependency-light (no geopandas needed just
to build a FeatureCollection) since this is called on every map request.
"""
from typing import Any


def point_feature(lon: float, lat: float, properties: dict[str, Any]) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": properties,
    }


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}
