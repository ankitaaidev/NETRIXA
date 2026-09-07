"""
facilities — static industrial facility reference data.

Design note: status / thermalActivity30d / thermalActivity90d / nearbyEvents /
lastActivity from the frontend's Facility type are NOT stored as columns
here. They are derived from thermal_events + event_analysis at query time
(Phase 9's /api/facilities endpoint), because storing them would duplicate
data that goes stale the moment a new detection arrives.
"""
import enum

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, Index, String, func

from app.database.session import Base
from app.models.enums import pg_enum


class FacilityCategory(str, enum.Enum):
    """Normalized taxonomy from the master build spec, used for backend
    filtering. Independent of `facility_type`, which stores the frontend's
    free-text display label (e.g. "Steel Plant") verbatim."""

    REFINERY = "refinery"
    PETROCHEMICAL = "petrochemical"
    THERMAL_POWER = "thermal_power"
    STEEL = "steel"
    MINING = "mining"
    LNG = "lng"
    OTHER = "other"


class Facility(Base):
    __tablename__ = "facilities"

    facility_id = Column(String, primary_key=True)  # e.g. "FAC-001"
    name = Column(String, nullable=False)

    # Free-text display label, matches frontend Facility.facilityType verbatim
    # (e.g. "Steel Plant", "LNG Terminal") so the UI needs no translation.
    facility_type = Column(String, nullable=False)

    # Normalized category for backend filtering per Phase 9 spec; nullable
    # since not every demo facility needs to map cleanly onto it yet.
    facility_category = Column(pg_enum(FacilityCategory, "facility_category"), nullable=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # spatial_index=False: GIST index declared explicitly in __table_args__ below.
    geom = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False)

    state = Column(String, nullable=False)
    district = Column(String, nullable=False)

    source = Column(String, nullable=False, default="DEMO")  # "OSM" | "MANUAL" | "DEMO"

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_facilities_geom", "geom", postgresql_using="gist"),
        Index("ix_facilities_state", "state"),
    )
