from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.alert import Alert
from app.models.enums import AlertStatus
from app.schemas.events import AlertOut

router = APIRouter()


def _serialize_alert(alert: Alert) -> AlertOut:
    return AlertOut(
        id=alert.alert_id,
        eventId=alert.event_id,
        severity=alert.severity.value,
        title=alert.title,
        message=alert.message,
        status=alert.status.value,
        createdAt=alert.created_at.isoformat(),
        resolvedAt=alert.resolved_at.isoformat() if alert.resolved_at else None,
        recommendedAction=alert.recommended_action,
    )


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(db: Session = Depends(get_db), status: str | None = None):
    stmt = select(Alert).order_by(Alert.created_at.desc())
    if status and status != "ALL":
        stmt = stmt.where(Alert.status == status)
    alerts = db.execute(stmt).scalars().all()
    return [_serialize_alert(a) for a in alerts]


@router.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return _serialize_alert(alert)
