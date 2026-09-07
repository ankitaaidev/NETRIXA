"""
event_analysis — the derived intelligence layer (AI classification + risk
assessment) computed on top of a raw thermal_events row.

This intentionally goes beyond the master plan's minimal field list
(event_id, classification, confidence, probability_distribution, risk_score,
risk_level, persistence_score, anomaly_score, historical_deviation,
industrial_proximity, spatial_change_score, explanation, recommended_action,
created_at) — all of those are present — plus additional columns the
shipped frontend actually renders (historical_mean, historical_std, z_score,
observations, first/last_observed, and a facility-attribution snapshot).

Rationale: the frontend's ThermalEvent type displays these directly per
event (Dashboard preview panel, EventDetail tabs, Reports). Recomputing
them from scratch on every request would be wasteful for a prototype;
storing the latest computed snapshot here (refreshed whenever Phase 6/7/8
services re-run) is the pragmatic middle ground. thermal_events itself
stays untouched/raw.

Two numeric "*_score" risk-formula components co-exist with categorical
labels the frontend needs (persistence vs persistence_score, spatial_change
vs spatial_change_score) — this is intentional, not duplication: the score
feeds the Phase 8 risk formula, the categorical label feeds the UI badge.

One-to-one with thermal_events for this prototype (unique event_id) —
re-analysis overwrites rather than versioning history.
"""
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.enums import (
    ClassificationType,
    PersistenceType,
    ProximityLevel,
    RiskLevel,
    SpatialChangeLevel,
    pg_enum,
)


class EventAnalysis(Base):
    __tablename__ = "event_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, ForeignKey("thermal_events.event_id", ondelete="CASCADE"), nullable=False)

    # --- Master-spec required fields ---
    classification = Column(pg_enum(ClassificationType, "classification_type"), nullable=False)
    confidence = Column(Float, nullable=False)  # classification confidence, 0-100
    probability_distribution = Column(JSONB, nullable=False)  # Dict[str, float]
    risk_score = Column(Integer, nullable=False)  # 0-100
    risk_level = Column(pg_enum(RiskLevel, "risk_level"), nullable=False)
    persistence_score = Column(Float, nullable=False)  # risk-formula component, 0-1
    anomaly_score = Column(Float, nullable=False)  # 0-1
    historical_deviation = Column(Float, nullable=False)  # matches frontend currentDeviation
    industrial_proximity = Column(pg_enum(ProximityLevel, "proximity_level"), nullable=False)
    spatial_change_score = Column(Float, nullable=False)  # risk-formula component, 0-1
    explanation = Column(JSONB, nullable=False)  # List[ExplanationFactor]
    recommended_action = Column(String, nullable=False)

    # --- Added for frontend compatibility (see module docstring) ---
    persistence = Column(pg_enum(PersistenceType, "persistence_type"), nullable=False)
    spatial_change = Column(pg_enum(SpatialChangeLevel, "spatial_change_level"), nullable=False)
    historical_mean = Column(Float, nullable=True)
    historical_std = Column(Float, nullable=True)
    z_score = Column(Float, nullable=True)
    observations = Column(Integer, nullable=False, default=1)
    first_observed = Column(Date, nullable=True)
    last_observed = Column(Date, nullable=True)

    # Facility attribution snapshot (computed by Phase 5 geospatial service
    # at analysis time; not a live FK, see thermal_event.py docstring).
    facility_name = Column(String, nullable=True)
    facility_distance = Column(Float, nullable=True)  # meters
    facility_type = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    event = relationship("ThermalEvent", back_populates="analysis")

    __table_args__ = (UniqueConstraint("event_id", name="uq_event_analysis_event_id"),)
