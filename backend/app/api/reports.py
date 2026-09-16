from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.event_analysis import EventAnalysis
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.schemas.serializers import serialize_event

router = APIRouter()


@router.post("/reports/events/{event_id}")
def generate_report(event_id: str, db: Session = Depends(get_db)):
    event = db.get(ThermalEvent, event_id)

    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id} not found.",
        )

    analysis = db.execute(
        select(EventAnalysis).where(EventAnalysis.event_id == event_id)
    ).scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=409,
            detail=f"Event {event_id} has not been analyzed yet.",
        )

    observations = db.execute(
        select(HistoricalObservation)
        .where(HistoricalObservation.event_id == event_id)
    ).scalars().all()

    return {
        "reportType": "NETRIXA Intelligence Report - Prototype",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "PROTOTYPE - classification and risk scoring are indicative, "
            "not production-validated. Intended for human review."
        ),
        "event": serialize_event(
            event,
            analysis,
            observations,
        ).model_dump(),
    }


@router.get("/reports/events/{event_id}/pdf")
def download_report_pdf(event_id: str, db: Session = Depends(get_db)):
    event = db.get(ThermalEvent, event_id)

    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id} not found.",
        )

    analysis = db.execute(
        select(EventAnalysis).where(
            EventAnalysis.event_id == event_id
        )
    ).scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=409,
            detail=f"Event {event_id} has not been analyzed yet.",
        )

    observations = db.execute(
        select(HistoricalObservation)
        .where(HistoricalObservation.event_id == event_id)
        .order_by(HistoricalObservation.obs_date)
    ).scalars().all()

    serialized = serialize_event(
        event,
        analysis,
        observations,
    )

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    pdf.setTitle(
        f"NETRIXA Intelligence Report - {event.event_id}"
    )

    # Title
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "NETRIXA INTELLIGENCE REPORT")

    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        50,
        y,
        "Thermal Intelligence Center - Prototype",
    )

    y -= 35

    # Event identification
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "1. EVENT IDENTIFICATION")

    y -= 20

    pdf.setFont("Helvetica", 10)

    event_details = [
        ("Event ID", serialized.eventId),
        ("Classification", serialized.classification),
        ("Risk Level", serialized.riskLevel),
        ("Risk Score", f"{serialized.riskScore} / 100"),
        ("Detection Confidence", f"{serialized.confidence}%"),
        (
            "Coordinates",
            f"{serialized.latitude:.4f} N, "
            f"{serialized.longitude:.4f} E",
        ),
        (
            "Detection Time",
            f"{serialized.acquisitionDate} "
            f"{serialized.acquisitionTime}",
        ),
        (
            "Satellite / Instrument",
            f"{serialized.satellite} / "
            f"{serialized.instrument}",
        ),
    ]

    for label, value in event_details:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(55, y, f"{label}:")

        pdf.setFont("Helvetica", 9)
        pdf.drawString(180, y, str(value))

        y -= 16

    # Thermal analysis
    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "2. THERMAL ANALYSIS")

    y -= 20

    thermal_details = [
        (
            "Brightness Temperature",
            f"{serialized.brightnessTemperature} K",
        ),
        (
            "Fire Radiative Power",
            f"{serialized.frp} MW",
        ),
        (
            "Historical Mean",
            f"{serialized.historicalMean} K",
        ),
        (
            "z-Score Deviation",
            f"{serialized.zScore:.2f}",
        ),
        (
            "Land Cover",
            str(serialized.landCover),
        ),
        (
            "Anomaly Score",
            f"{serialized.anomalyScore * 100:.0f} / 100",
        ),
    ]

    for label, value in thermal_details:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(55, y, f"{label}:")

        pdf.setFont("Helvetica", 9)
        pdf.drawString(180, y, str(value))

        y -= 16

    # Facility
    if serialized.facilityName:
        y -= 15

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "3. FACILITY INFORMATION")

        y -= 20

        facility_details = [
            ("Facility Name", serialized.facilityName),
            (
                "Facility Type",
                serialized.facilityType or "-",
            ),
            (
                "Distance",
                f"{serialized.facilityDistance} m",
            ),
            (
                "Industrial Proximity",
                serialized.industrialProximity,
            ),
        ]

        for label, value in facility_details:
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(55, y, f"{label}:")

            pdf.setFont("Helvetica", 9)
            pdf.drawString(180, y, str(value))

            y -= 16

    # Classification
    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(
        50,
        y,
        "4. AI CLASSIFICATION EXPLANATION",
    )

    y -= 20

    for factor in serialized.explanation:
        if factor.confirmed:
            pdf.setFont("Helvetica", 9)
            text = (
                f"- {factor.factor}: "
                f"{factor.description}"
            )

            # Keep long explanation inside page width
            if len(text) > 110:
                text = text[:107] + "..."

            pdf.drawString(55, y, text)
            y -= 15

    # Recommended action
    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(
        50,
        y,
        "5. RECOMMENDED ACTION",
    )

    y -= 20

    pdf.setFont("Helvetica", 10)

    action = serialized.recommendedAction or "-"

    if len(action) > 100:
        action = action[:97] + "..."

    pdf.drawString(55, y, action)

    # Footer
    y -= 40

    pdf.setFont("Helvetica", 8)
    pdf.drawString(
        50,
        y,
        "Prototype - classification and risk scoring are "
        "indicative, not production-validated.",
    )

    pdf.save()

    buffer.seek(0)

    filename = (
        f"netrixa-report-{event.event_id}.pdf"
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )