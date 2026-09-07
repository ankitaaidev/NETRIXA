"""
Keeps each model's `geom` PostGIS column in sync with its `latitude` /
`longitude` scalar columns automatically, so calling code (seed scripts,
ingestion services) only ever needs to set latitude/longitude and never
has to remember to construct a WKT point by hand.

Imported once from app.database.session's Base setup via app.models
package import; registered against every mapped class that defines both
`latitude`/`longitude` and `geom`.
"""
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import event

from app.models.facility import Facility
from app.models.thermal_event import ThermalEvent

_GEO_MODELS = (ThermalEvent, Facility)


def _sync_geom(mapper, connection, target):  # noqa: ARG001 - SQLAlchemy event signature
    if target.latitude is not None and target.longitude is not None:
        target.geom = from_shape(Point(target.longitude, target.latitude), srid=4326)


def register_geo_listeners() -> None:
    for model in _GEO_MODELS:
        event.listen(model, "before_insert", _sync_geom)
        event.listen(model, "before_update", _sync_geom)
