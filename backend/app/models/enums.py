"""
Enums shared across models.

IMPORTANT: These values are intentionally matched character-for-character
to the frontend's src/types/index.ts union types, since that frontend is
the authoritative UI and Phase 10 will wire these responses directly into
it without a translation layer.

Where the NETRIXA master build prompt's classification list differs
slightly from what the shipped frontend actually uses (e.g. the frontend
has a distinct "Industrial Fire" in addition to "Potential Industrial
Fire", and uses "Mining Activity" / "Unknown / Insufficient Evidence"
rather than "Mining/Other" / "Unknown"), we follow the frontend's set,
since preserving the existing UI is the top priority for this project.
"""
import enum

from sqlalchemy import Enum


def pg_enum(enum_cls, name: str) -> Enum:
    """
    Consistent helper for every enum column in this project.

    By default SQLAlchemy's Enum type persists the Python enum MEMBER NAME
    (e.g. "PERSISTENT_INDUSTRIAL_THERMAL_SOURCE") rather than its .value
    (e.g. "Persistent Industrial Thermal Source"). Since these enum values
    are intentionally matched to the frontend's TypeScript string unions
    (see module docstring below), we must store the .value, not the name,
    or every classification/risk-level/etc. string leaving the API would
    silently mismatch what the frontend expects.
    """
    return Enum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj])


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ClassificationType(str, enum.Enum):
    POTENTIAL_INDUSTRIAL_FIRE = "Potential Industrial Fire"
    INDUSTRIAL_FIRE = "Industrial Fire"
    PERSISTENT_INDUSTRIAL_THERMAL_SOURCE = "Persistent Industrial Thermal Source"
    GAS_FLARE = "Gas Flare"
    AGRICULTURAL_BURNING = "Agricultural Burning"
    WILDFIRE = "Wildfire"
    MINING_ACTIVITY = "Mining Activity"
    UNKNOWN = "Unknown / Insufficient Evidence"


class PersistenceType(str, enum.Enum):
    NORMAL_PERSISTENT = "NORMAL_PERSISTENT"
    ABNORMAL_PERSISTENT = "ABNORMAL_PERSISTENT"
    SUDDEN_EVENT = "SUDDEN_EVENT"
    INTERMITTENT = "INTERMITTENT"
    UNKNOWN = "UNKNOWN"


class ProximityLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class SpatialChangeLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    STABLE = "STABLE"


class FacilityStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    ABNORMAL = "ABNORMAL"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class FeedbackDecision(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
