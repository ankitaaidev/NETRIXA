"""
ThermalClassifier (Phase 7).

There is no labeled training dataset available for this prototype, so per
the master plan's explicit instruction we implement a DETERMINISTIC,
EXPLAINABLE rule-based scoring system rather than a trained ML model —
and we make no claim about "accuracy" anywhere, since that would require
a held-out labeled test set we don't have.

Design: each candidate classification has a scoring function built from
simple, human-readable feature comparisons (land cover, facility
proximity, persistence pattern, z-score, brightness temperature, FRP).
Scores are turned into a probability distribution via softmax, so the
output has the *shape* of a probabilistic classifier (probability
distribution, confidence) while remaining fully deterministic and
auditable — every score contribution can be read directly from the code
and is surfaced again in `explain()`.
"""
import math
from dataclasses import dataclass, field

from app.models.enums import ClassificationType, PersistenceType, ProximityLevel


@dataclass
class ClassifierFeatures:
    brightness_temperature: float
    frp: float
    confidence: float  # raw satellite detection confidence, 0-100
    facility_distance_m: float | None
    facility_proximity: ProximityLevel
    land_cover: str
    historical_mean: float
    historical_std: float
    z_score: float
    persistence: PersistenceType
    recurrence_rate: float
    observations: int


@dataclass
class ExplanationFactor:
    factor: str
    value: str  # "HIGH" | "MEDIUM" | "LOW"
    confirmed: bool
    description: str


@dataclass
class ClassificationResult:
    classification: ClassificationType
    confidence: float  # 0-100, derived from the winning class's softmax probability
    probability_distribution: dict[str, float]
    explanation: list[ExplanationFactor] = field(default_factory=list)


SOFTMAX_TEMPERATURE = 1.6


def _score_potential_industrial_fire(f: ClassifierFeatures) -> float:
    if f.land_cover != "Industrial":
        return 0.0
    score = 0.0
    if f.facility_proximity in (ProximityLevel.HIGH, ProximityLevel.MEDIUM):
        score += 1.0
    if f.persistence == PersistenceType.SUDDEN_EVENT:
        score += 2.0
    score += max(0.0, min(f.z_score, 8.0)) * 0.5
    if f.frp > 100:
        score += 1.5
    if f.brightness_temperature > 390:
        score += 1.5
    return score


def _score_industrial_fire(f: ClassifierFeatures) -> float:
    if f.land_cover != "Industrial":
        return 0.0
    score = 0.0
    if f.facility_proximity in (ProximityLevel.HIGH, ProximityLevel.MEDIUM):
        score += 1.0
    if f.persistence == PersistenceType.ABNORMAL_PERSISTENT:
        score += 2.0
    score += max(0.0, min(f.z_score, 6.0)) * 0.4
    if 45 < f.frp <= 120:
        score += 1.0
    return score


def _score_persistent_industrial(f: ClassifierFeatures) -> float:
    if f.land_cover != "Industrial":
        return 0.0
    score = 0.0
    if f.facility_proximity in (ProximityLevel.HIGH, ProximityLevel.MEDIUM):
        score += 1.0
    if f.persistence == PersistenceType.NORMAL_PERSISTENT:
        score += 1.5
    if abs(f.z_score) < 1.0:
        score += 1.0
    if 335 <= f.brightness_temperature <= 365 and f.frp < 100:
        score += 1.5
    return score


def _score_gas_flare(f: ClassifierFeatures) -> float:
    if f.land_cover != "Industrial":
        return 0.0
    score = 0.0
    if f.facility_proximity in (ProximityLevel.HIGH, ProximityLevel.MEDIUM):
        score += 1.0
    if f.persistence == PersistenceType.NORMAL_PERSISTENT:
        score += 1.0
    if f.brightness_temperature > 365 and f.frp < 40:
        score += 3.5
    return score


def _score_agricultural_burning(f: ClassifierFeatures) -> float:
    score = 0.0
    if f.land_cover == "Cropland":
        score += 3.0
    if 310 <= f.brightness_temperature <= 350 and f.frp < 45:
        score += 1.0
    return score


def _score_wildfire(f: ClassifierFeatures) -> float:
    score = 0.0
    if f.land_cover == "Forest":
        score += 3.0
    if f.z_score > 1.0:
        score += 0.5
    return score


def _score_mining(f: ClassifierFeatures) -> float:
    score = 0.0
    if f.land_cover == "Barren/Mining":
        score += 3.0
    return score


def _score_unknown(f: ClassifierFeatures) -> float:
    score = 0.3  # small constant floor so it can win when nothing else matches
    if f.confidence < 60:
        score += 1.5
    if f.persistence == PersistenceType.UNKNOWN:
        score += 1.5
    if f.land_cover == "Mixed/Unclassified":
        score += 1.0
    return score


_SCORERS: dict[ClassificationType, callable] = {
    ClassificationType.POTENTIAL_INDUSTRIAL_FIRE: _score_potential_industrial_fire,
    ClassificationType.INDUSTRIAL_FIRE: _score_industrial_fire,
    ClassificationType.PERSISTENT_INDUSTRIAL_THERMAL_SOURCE: _score_persistent_industrial,
    ClassificationType.GAS_FLARE: _score_gas_flare,
    ClassificationType.AGRICULTURAL_BURNING: _score_agricultural_burning,
    ClassificationType.WILDFIRE: _score_wildfire,
    ClassificationType.MINING_ACTIVITY: _score_mining,
    ClassificationType.UNKNOWN: _score_unknown,
}


class ThermalClassifier:
    """Deterministic, rule-based, explainable prototype classifier.
    No trained weights, no claimed accuracy — see module docstring."""

    def _scores(self, features: ClassifierFeatures) -> dict[ClassificationType, float]:
        return {cls: scorer(features) for cls, scorer in _SCORERS.items()}

    def predict(self, features: ClassifierFeatures) -> ClassificationResult:
        scores = self._scores(features)
        max_score = max(scores.values())
        exp_scores = {cls: math.exp((s - max_score) / SOFTMAX_TEMPERATURE) for cls, s in scores.items()}
        total = sum(exp_scores.values())
        probabilities = {cls.value: round(s / total, 4) for cls, s in exp_scores.items()}

        winning_class = max(scores, key=scores.get)
        confidence = round(probabilities[winning_class.value] * 100, 1)

        return ClassificationResult(
            classification=winning_class,
            confidence=confidence,
            probability_distribution=probabilities,
            explanation=self.explain(features, winning_class),
        )

    def explain(self, features: ClassifierFeatures, classification: ClassificationType | None = None) -> list[ExplanationFactor]:
        f = features
        if classification is None:
            classification = self.predict(features).classification

        factors: list[ExplanationFactor] = []

        factors.append(ExplanationFactor(
            factor="Land cover",
            value="HIGH" if f.land_cover != "Mixed/Unclassified" else "LOW",
            confirmed=f.land_cover != "Mixed/Unclassified",
            description=f"Detection site land cover classified as {f.land_cover}.",
        ))

        if f.facility_proximity != ProximityLevel.NONE:
            factors.append(ExplanationFactor(
                factor="Industrial proximity",
                value=f.facility_proximity.value,
                confirmed=f.facility_proximity in (ProximityLevel.HIGH, ProximityLevel.MEDIUM),
                description=(
                    f"Nearest industrial facility ~{f.facility_distance_m:.0f} m away."
                    if f.facility_distance_m is not None else "No nearby industrial facility identified."
                ),
            ))

        z_value = "HIGH" if abs(f.z_score) >= 2 else "MEDIUM" if abs(f.z_score) >= 1 else "LOW"
        factors.append(ExplanationFactor(
            factor="Historical deviation",
            value=z_value,
            confirmed=abs(f.z_score) >= 1,
            description=f"Current reading deviates {f.z_score:+.2f}σ from this site's historical baseline "
                        f"({f.historical_mean:.1f}K ± {f.historical_std:.1f}K).",
        ))

        factors.append(ExplanationFactor(
            factor="Persistence pattern",
            value="HIGH" if f.persistence in (PersistenceType.SUDDEN_EVENT, PersistenceType.ABNORMAL_PERSISTENT) else "LOW",
            confirmed=f.persistence != PersistenceType.UNKNOWN,
            description=f"Temporal pattern classified as {f.persistence.value} "
                        f"across {f.observations} days of history (recurrence {f.recurrence_rate:.0%}).",
        ))

        factors.append(ExplanationFactor(
            factor="Fire Radiative Power",
            value="HIGH" if f.frp > 100 else "MEDIUM" if f.frp > 40 else "LOW",
            confirmed=f.frp > 40,
            description=f"FRP measured at {f.frp:.1f} MW.",
        ))

        return factors
