"""
analyst_feedback — human-in-the-loop verdicts on an event's AI
classification, submitted via POST /api/events/{event_id}/feedback (Phase 9).

The master plan lists `decision` without enumerating values; CONFIRMED /
FALSE_POSITIVE / NEEDS_REVIEW are a reasonable prototype default and are
easy to extend later.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.enums import FeedbackDecision, pg_enum


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, ForeignKey("thermal_events.event_id", ondelete="CASCADE"), nullable=False)

    decision = Column(pg_enum(FeedbackDecision, "feedback_decision"), nullable=False)
    analyst_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event = relationship("ThermalEvent", back_populates="feedback")
