"""
historical_observations — daily thermal baseline series backing z-score /
persistence calculations (Phase 6 temporal_service) and the frontend's
per-event historicalData chart.

Design note: tied to event_id (one series per event), matching how the
shipped frontend actually consumes this data (ThermalEvent.historicalData
is a property of a single event). A more normalized design would key this
to a persistent "site" concept shared across repeated detections at the
same physical location, but that's a bigger modeling change than this
prototype's scope — documented here as a known simplification.
"""
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database.session import Base


class HistoricalObservation(Base):
    __tablename__ = "historical_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, ForeignKey("thermal_events.event_id", ondelete="CASCADE"), nullable=False)

    obs_date = Column(Date, nullable=False)
    intensity = Column(Float, nullable=False)  # brightness temperature (K) on that date
    frp = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event = relationship("ThermalEvent", back_populates="historical_observations")

    __table_args__ = (
        UniqueConstraint("event_id", "obs_date", name="uq_historical_obs_event_date"),
        Index("ix_historical_obs_event_id", "event_id"),
    )
