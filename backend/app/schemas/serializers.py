"""
Assembles ThermalEvent + EventAnalysis (+ optional historical observations)
into the frontend-facing ThermalEventOut shape. Centralized here so every
endpoint (list, detail, map, priority) produces identically-shaped output.
"""
from app.models.event_analysis import EventAnalysis
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent
from app.schemas.events import ExplanationFactorOut, HistoricalPointOut, ThermalEventOut


def serialize_event(
    event: ThermalEvent,
    analysis: EventAnalysis | None,
    historical_observations: list[HistoricalObservation] | None = None,
) -> ThermalEventOut:
    dt = event.detection_time
    acquisition_date = dt.strftime("%Y-%m-%d")
    acquisition_time = dt.strftime("%H:%M UTC")

    if analysis is None:
        # Raw event ingested but not yet processed by the pipeline —
        # surface it honestly as unanalyzed rather than inventing values.
        return ThermalEventOut(
            id=event.event_id, eventId=event.event_id,
            latitude=event.latitude, longitude=event.longitude,
            acquisitionDate=acquisition_date, acquisitionTime=acquisition_time,
            brightnessTemperature=event.brightness_temperature, frp=event.frp,
            confidence=event.confidence, satellite=event.satellite, instrument=event.instrument,
            classification="Unknown / Insufficient Evidence", riskScore=0, riskLevel="LOW",
            state=event.state, district=event.district, landCover=event.land_cover,
            historicalMean=None, historicalStd=None, currentDeviation=0.0, zScore=0.0,
            persistence="UNKNOWN", observations=0, firstObserved=None, lastObserved=None,
            anomalyScore=0.0, industrialProximity="NONE", explanation=[],
            classificationProbabilities={}, recommendedAction="Not yet analyzed.",
            spatialChange="LOW", historicalData=[],
        )

    explanation = [
        ExplanationFactorOut(factor=f["factor"], value=f["value"], confirmed=f["confirmed"], description=f["description"])
        for f in (analysis.explanation or [])
    ]

    historical_data = []
    if historical_observations:
        historical_data = [
            HistoricalPointOut(
                date=o.obs_date.strftime("%Y-%m-%d"),
                intensity=o.intensity, frp=o.frp, isAnomaly=o.is_anomaly,
            )
            for o in sorted(historical_observations, key=lambda o: o.obs_date)
        ]

    return ThermalEventOut(
        id=event.event_id,
        eventId=event.event_id,
        latitude=event.latitude,
        longitude=event.longitude,
        acquisitionDate=acquisition_date,
        acquisitionTime=acquisition_time,
        brightnessTemperature=event.brightness_temperature,
        frp=event.frp,
        confidence=event.confidence,
        satellite=event.satellite,
        instrument=event.instrument,
        classification=analysis.classification.value,
        riskScore=analysis.risk_score,
        riskLevel=analysis.risk_level.value,
        state=event.state,
        district=event.district,
        facilityName=analysis.facility_name,
        facilityDistance=analysis.facility_distance,
        facilityType=analysis.facility_type,
        landCover=event.land_cover,
        historicalMean=analysis.historical_mean,
        historicalStd=analysis.historical_std,
        currentDeviation=analysis.historical_deviation,
        zScore=analysis.z_score or 0.0,
        persistence=analysis.persistence.value,
        observations=analysis.observations,
        firstObserved=analysis.first_observed.strftime("%Y-%m-%d") if analysis.first_observed else None,
        lastObserved=analysis.last_observed.strftime("%Y-%m-%d") if analysis.last_observed else None,
        anomalyScore=analysis.anomaly_score,
        industrialProximity=analysis.industrial_proximity.value,
        explanation=explanation,
        classificationProbabilities=analysis.probability_distribution or {},
        recommendedAction=analysis.recommended_action,
        spatialChange=analysis.spatial_change.value,
        historicalData=historical_data,
    )
