from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import ClassificationType, ProximityLevel, RiskLevel, PersistenceType
from app.models.event_analysis import EventAnalysis
from app.models.thermal_event import ThermalEvent
from app.schemas.events import DashboardSummaryOut

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummaryOut)
def dashboard_summary(db: Session = Depends(get_db)):
    total_events = db.execute(select(func.count(ThermalEvent.event_id))).scalar() or 0

    industrial_events = db.execute(
        select(func.count(EventAnalysis.id)).where(
            EventAnalysis.industrial_proximity.in_([ProximityLevel.HIGH, ProximityLevel.MEDIUM])
        )
    ).scalar() or 0

    potential_industrial_fires = db.execute(
        select(func.count(EventAnalysis.id)).where(
            EventAnalysis.classification.in_([ClassificationType.POTENTIAL_INDUSTRIAL_FIRE, ClassificationType.INDUSTRIAL_FIRE])
        )
    ).scalar() or 0

    critical_events = db.execute(
        select(func.count(EventAnalysis.id)).where(EventAnalysis.risk_level == RiskLevel.CRITICAL)
    ).scalar() or 0

    persistent_sources = db.execute(
        select(func.count(EventAnalysis.id)).where(EventAnalysis.persistence == PersistenceType.NORMAL_PERSISTENT)
    ).scalar() or 0

    return DashboardSummaryOut(
        totalEvents=total_events,
        industrialEvents=industrial_events,
        potentialIndustrialFires=potential_industrial_fires,
        criticalEvents=critical_events,
        persistentSources=persistent_sources,
    )
