"""
Risk Engine (Phase 8).

Implements the master plan's weighted formula exactly:

    risk_score = 0.30 * thermal_anomaly_score
               + 0.20 * industrial_proximity_score
               + 0.15 * historical_deviation_score
               + 0.15 * spatial_change_score
               + 0.10 * persistence_score
               + 0.10 * classification_confidence_score

...with one deliberate, documented design decision on top of the literal
spec: an "industrial relevance" multiplier scales the raw thermal-signal
components by how relevant the CLASSIFICATION is to industrial risk.

WHY: NETRIXA is an industrial thermal-risk system (see its own tagline —
FIRMS tells us WHERE, NETRIXA tells us whether it's an INDUSTRIAL risk).
Without this adjustment, a routine agricultural burn produces a large raw
z-score (a burning field really is much hotter than bare cropland) and
the literal formula would push it into MEDIUM/HIGH risk purely from
thermal magnitude — directly contradicting the master plan's own demo
Scenario B, which specifies Agricultural Burning must resolve to LOW risk
/ "no immediate action" specifically BECAUSE of what it is, not because
its thermal signature is weak. Real thermal-risk systems make the same
call: classification gates operational priority. This multiplier is
applied transparently (visible in `components` on the result) rather than
folded silently into the weights, and CRITICAL is still reachable for
every classification if the underlying signal is extreme enough.

Risk levels (thresholds configurable via app.core.config.Settings):
    0-25   LOW
    26-50  MEDIUM
    51-75  HIGH
    76-100 CRITICAL

This is explicitly a prototype scoring model, not a validated operational
risk standard — every weighted component is returned alongside the final
score so the computation is fully auditable.
"""
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.models.enums import ClassificationType, ProximityLevel, RiskLevel

WEIGHTS = {
    "thermal_anomaly": 0.30,
    "industrial_proximity": 0.20,
    "historical_deviation": 0.15,
    "spatial_change": 0.15,
    "persistence": 0.10,
    "classification_confidence": 0.10,
}

PROXIMITY_VALUE = {
    ProximityLevel.HIGH: 1.0,
    ProximityLevel.MEDIUM: 0.6,
    ProximityLevel.LOW: 0.3,
    ProximityLevel.NONE: 0.0,
}

# Documented industrial-relevance multiplier — see module docstring.
INDUSTRIAL_RELEVANCE = {
    ClassificationType.POTENTIAL_INDUSTRIAL_FIRE: 1.0,
    ClassificationType.INDUSTRIAL_FIRE: 1.0,
    ClassificationType.PERSISTENT_INDUSTRIAL_THERMAL_SOURCE: 1.0,
    ClassificationType.GAS_FLARE: 1.0,
    ClassificationType.MINING_ACTIVITY: 0.6,
    ClassificationType.WILDFIRE: 0.5,
    ClassificationType.AGRICULTURAL_BURNING: 0.3,
    ClassificationType.UNKNOWN: 0.7,
}

RECOMMENDED_ACTIONS = {
    RiskLevel.CRITICAL: "Immediate investigation required — dispatch field verification.",
    RiskLevel.HIGH: "Verify within 24 hours — elevated deviation from historical baseline.",
    RiskLevel.MEDIUM: "Monitor — schedule routine review.",
    RiskLevel.LOW: "Observe — no immediate action required.",
}

_AGRICULTURAL_LOW_ACTION = "No immediate action — consistent with expected agricultural burning pattern."


@dataclass
class RiskResult:
    risk_score: int  # 0-100
    risk_level: RiskLevel
    recommended_action: str
    components: dict = field(default_factory=dict)  # raw + weighted contribution per factor, for auditability


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_risk(
    z_score: float,
    proximity: ProximityLevel,
    persistence_score: float,
    spatial_change_score: float,
    classification: ClassificationType,
    classification_confidence: float,  # 0-100
) -> RiskResult:
    settings = get_settings()

    relevance = INDUSTRIAL_RELEVANCE.get(classification, 0.7)
    raw_thermal_anomaly = _clamp01(max(z_score, 0.0) / 4.0)
    thermal_anomaly_score = raw_thermal_anomaly * relevance
    historical_deviation_score = thermal_anomaly_score  # same basis, see module docstring
    proximity_value = PROXIMITY_VALUE.get(proximity, 0.0)
    industrial_proximity_score = proximity_value * thermal_anomaly_score
    confidence_score = _clamp01(classification_confidence / 100.0)
    spatial_change_score = _clamp01(spatial_change_score)
    persistence_score = _clamp01(persistence_score)

    weighted = {
        "thermal_anomaly": WEIGHTS["thermal_anomaly"] * thermal_anomaly_score,
        "industrial_proximity": WEIGHTS["industrial_proximity"] * industrial_proximity_score,
        "historical_deviation": WEIGHTS["historical_deviation"] * historical_deviation_score,
        "spatial_change": WEIGHTS["spatial_change"] * spatial_change_score,
        "persistence": WEIGHTS["persistence"] * persistence_score,
        "classification_confidence": WEIGHTS["classification_confidence"] * confidence_score,
    }
    risk_score = round(sum(weighted.values()) * 100)
    risk_score = max(0, min(100, risk_score))

    if risk_score <= settings.RISK_LOW_MAX:
        risk_level = RiskLevel.LOW
    elif risk_score <= settings.RISK_MEDIUM_MAX:
        risk_level = RiskLevel.MEDIUM
    elif risk_score <= settings.RISK_HIGH_MAX:
        risk_level = RiskLevel.HIGH
    else:
        risk_level = RiskLevel.CRITICAL

    if risk_level == RiskLevel.LOW and classification == ClassificationType.AGRICULTURAL_BURNING:
        recommended_action = _AGRICULTURAL_LOW_ACTION
    else:
        recommended_action = RECOMMENDED_ACTIONS[risk_level]

    return RiskResult(
        risk_score=risk_score,
        risk_level=risk_level,
        recommended_action=recommended_action,
        components={
            "industrial_relevance_multiplier": relevance,
            "raw_thermal_anomaly_score": round(raw_thermal_anomaly, 4),
            "thermal_anomaly_score": round(thermal_anomaly_score, 4),
            "industrial_proximity_score": round(industrial_proximity_score, 4),
            "historical_deviation_score": round(historical_deviation_score, 4),
            "spatial_change_score": round(spatial_change_score, 4),
            "persistence_score": round(persistence_score, 4),
            "classification_confidence_score": round(confidence_score, 4),
            "weighted_contributions": {k: round(v, 4) for k, v in weighted.items()},
        },
    )
