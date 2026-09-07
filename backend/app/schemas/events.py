"""
Response schemas.

Field names here are intentionally camelCase, matching src/types/index.ts
in the frontend verbatim (ThermalEvent, Facility, Alert, DashboardSummary,
ExplanationFactor, HistoricalPoint) rather than following PEP8 snake_case.
This is deliberate: Phase 10 wires these responses directly into the
existing frontend, and any naming mismatch would force a translation
layer we specifically want to avoid.
"""
from pydantic import BaseModel, Field


class ExplanationFactorOut(BaseModel):
    factor: str
    value: str
    confirmed: bool
    description: str


class HistoricalPointOut(BaseModel):
    date: str
    intensity: float
    frp: float
    isAnomaly: bool | None = None


class ThermalEventOut(BaseModel):
    id: str  # == eventId; kept for frontend compatibility until Phase 10 simplifies routing
    eventId: str
    latitude: float
    longitude: float
    acquisitionDate: str
    acquisitionTime: str
    brightnessTemperature: float
    frp: float
    confidence: float
    satellite: str
    instrument: str
    classification: str
    riskScore: int
    riskLevel: str
    state: str | None
    district: str | None
    facilityName: str | None = None
    facilityDistance: float | None = None
    facilityType: str | None = None
    landCover: str | None
    historicalMean: float | None
    historicalStd: float | None
    currentDeviation: float
    zScore: float
    persistence: str
    observations: int
    firstObserved: str | None
    lastObserved: str | None
    anomalyScore: float
    industrialProximity: str
    explanation: list[ExplanationFactorOut]
    classificationProbabilities: dict[str, float]
    recommendedAction: str
    spatialChange: str
    historicalData: list[HistoricalPointOut] = Field(default_factory=list)


class FacilityOut(BaseModel):
    id: str
    facilityId: str
    name: str
    facilityType: str
    latitude: float
    longitude: float
    state: str
    district: str
    status: str
    thermalActivity30d: int
    thermalActivity90d: int
    nearbyEvents: int
    lastActivity: str | None


class AlertOut(BaseModel):
    id: str
    eventId: str
    severity: str
    title: str
    message: str
    status: str
    createdAt: str
    resolvedAt: str | None = None
    recommendedAction: str


class DashboardSummaryOut(BaseModel):
    totalEvents: int
    industrialEvents: int
    potentialIndustrialFires: int
    criticalEvents: int
    persistentSources: int


class PaginatedEventsOut(BaseModel):
    items: list[ThermalEventOut]
    total: int
    page: int
    pageSize: int


class FeedbackIn(BaseModel):
    decision: str  # "CONFIRMED" | "FALSE_POSITIVE" | "NEEDS_REVIEW"
    analystNote: str | None = None
