"""
alerts — priority thermal-anomaly notifications shown in the frontend's
Alert Center.

`recommended_action` is not in the master plan's minimal field list but is
required by the frontend's Alert type (Alerts.tsx renders it directly) —
added here, documented per the same convention as event_analysis.
"""
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.enums import AlertStatus, RiskLevel, pg_enum


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True)  # e.g. "a1" / "NTX-ALERT-00001"
    event_id = Column(String, ForeignKey("thermal_events.event_id", ondelete="CASCADE"), nullable=False)

    severity = Column(pg_enum(RiskLevel, "alert_severity"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(pg_enum(AlertStatus, "alert_status"), nullable=False, default=AlertStatus.ACTIVE)
    recommended_action = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    event = relationship("ThermalEvent", back_populates="alerts")
