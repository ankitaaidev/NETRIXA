"""
thermal_events — raw thermal detection records (FIRMS-style, or demo-generated).

Design notes (deviations from the literal master-plan field list, made to
keep this schema honest and to match what the shipped frontend actually
needs — see Phase 1 audit report for full reasoning):

- event_id (e.g. "NTX-IND-00241") is the ONLY identifier, per the agreed
  decision — no separate numeric routing id.
- state / district / land_cover are included here (not in the master
  plan's minimal list) because the frontend filters/displays them per
  event, and they are natural attributes of a raw detection's location
  once geospatial context is attached (Phase 5 populates them).
- Facility attribution (name/distance/type) is deliberately NOT stored
  here — it's computed live via nearest-facility geospatial queries
  (Phase 5) and assembled into API responses (Phase 9), so it can't go
  stale relative to the facilities table.
"""
from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import relationship

from app.database.session import Base


class ThermalEvent(Base):
    __tablename__ = "thermal_events"

    event_id = Column(String, primary_key=True)  # e.g. "NTX-IND-00241"

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # spatial_index=False: we declare the GIST index explicitly in __table_args__
    # below to keep index naming/ownership consistent across all models rather
    # than relying on GeoAlchemy2's own auto-generated "idx_*" index.
    geom = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False)

    detection_time = Column(DateTime(timezone=True), nullable=False)

    brightness_temperature = Column(Float, nullable=False)
    frp = Column(Float, nullable=False)  # Fire Radiative Power (MW)
    confidence = Column(Float, nullable=False)  # raw satellite detection confidence, 0-100

    satellite = Column(String, nullable=False)
    instrument = Column(String, nullable=False)
    source = Column(String, nullable=False, default="DEMO")  # "FIRMS" | "DEMO"

    # Populated by the geospatial layer (Phase 5), nullable until then.
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    land_cover = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    analysis = relationship(
        "EventAnalysis", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    historical_observations = relationship(
        "HistoricalObservation", back_populates="event", cascade="all, delete-orphan"
    )
    alerts = relationship("Alert", back_populates="event", cascade="all, delete-orphan")
    feedback = relationship("AnalystFeedback", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_thermal_events_geom", "geom", postgresql_using="gist"),
        Index("ix_thermal_events_detection_time", "detection_time"),
        Index("ix_thermal_events_state", "state"),
    )
