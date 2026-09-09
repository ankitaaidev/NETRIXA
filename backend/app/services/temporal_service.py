"""
Historical Intelligence (Phase 6).

Computes, from a single event's historical_observations series:
  - historical mean / std (baseline, excluding already-flagged anomaly days)
  - current deviation and z-score of the live detection against that baseline
  - a persistence behavior classification (NORMAL_PERSISTENT / ABNORMAL_PERSISTENT
    / SUDDEN_EVENT / INTERMITTENT / UNKNOWN)
  - trend (increasing / decreasing / stable) over the last two weeks
  - recurrence rate (fraction of days flagged anomalous)
  - a "spatial_change" label

LIMITATION (documented): our schema ties historical_observations to a
single event_id (see historical_observation.py docstring) rather than a
shared physical "site" concept, so there's no true multi-detection
spatial-drift signal available. `spatial_change` here is a documented
proxy derived from the same anomaly pattern used for `persistence`, not
an independent spatial measurement — see module docstring for the
alternative (a "site" abstraction) that a production system should add.
"""
from dataclasses import dataclass
from datetime import date

from app.models.enums import PersistenceType, SpatialChangeLevel
from app.models.historical_observation import HistoricalObservation

EPSILON = 1e-6


@dataclass
class TemporalAnalysisResult:
    historical_mean: float
    historical_std: float
    z_score: float
    current_deviation: float
    persistence: PersistenceType
    persistence_score: float  # 0-1, risk-formula component
    spatial_change: SpatialChangeLevel
    spatial_change_score: float  # 0-1, risk-formula component
    observations: int
    first_observed: date | None
    last_observed: date | None
    trend: str  # "increasing" | "decreasing" | "stable"
    recurrence_rate: float  # fraction of observed days flagged anomalous


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def analyze_history(
    observations: list[HistoricalObservation],
    current_value: float,
) -> TemporalAnalysisResult:
    n = len(observations)

    if n == 0:
        return TemporalAnalysisResult(
            historical_mean=current_value, historical_std=0.0, z_score=0.0, current_deviation=0.0,
            persistence=PersistenceType.UNKNOWN, persistence_score=0.5,
            spatial_change=SpatialChangeLevel.LOW, spatial_change_score=0.3,
            observations=0, first_observed=None, last_observed=None,
            trend="stable", recurrence_rate=0.0,
        )

    observations_sorted = sorted(observations, key=lambda o: o.obs_date)
    baseline = [o for o in observations_sorted if not o.is_anomaly]
    anomalies = [o for o in observations_sorted if o.is_anomaly]

    reference = baseline if len(baseline) >= 5 else observations_sorted
    historical_mean = sum(o.intensity for o in reference) / len(reference)
    variance = sum((o.intensity - historical_mean) ** 2 for o in reference) / len(reference)
    historical_std = variance ** 0.5

    current_deviation = current_value - historical_mean

    # A z-score is not statistically meaningful when the historical
    # baseline has no variation. Keep the actual deviation, but neutralize
    # the z-score so it cannot create a false anomaly.
    if historical_std <= EPSILON:
        z_score = 0.0
    else:
        z_score = current_deviation / historical_std

    recurrence_rate = len(anomalies) / n

    # Trend: last 7 days vs the preceding 14 days.
    last_7 = observations_sorted[-7:]
    prior_14 = observations_sorted[-21:-7] if n >= 21 else observations_sorted[:-7]
    if prior_14:
        last_7_mean = sum(o.intensity for o in last_7) / len(last_7)
        prior_14_mean = sum(o.intensity for o in prior_14) / len(prior_14)
        if prior_14_mean > EPSILON:
            pct_change = (last_7_mean - prior_14_mean) / prior_14_mean
        else:
            pct_change = 0.0
        trend = "increasing" if pct_change > 0.10 else "decreasing" if pct_change < -0.10 else "stable"
    else:
        trend = "stable"

    # Compute the current anomaly streak: consecutive anomalous days
    # counting backward from the most recent observation. This correctly
    # distinguishes a short fresh spike (streak ~1-5 days -> SUDDEN_EVENT)
    # from a longer ongoing pattern (streak ~10+ days -> ABNORMAL_PERSISTENT)
    # regardless of how that streak compares to a fixed-size window.
    current_streak = 0
    for o in reversed(observations_sorted):
        if o.is_anomaly:
            current_streak += 1
        else:
            break

    if n < 5:
        persistence = PersistenceType.UNKNOWN
        persistence_score = 0.5
        spatial_change = SpatialChangeLevel.LOW
        spatial_change_score = 0.3
    elif abs(z_score) < 1.0 and recurrence_rate < 0.05:
        persistence = PersistenceType.NORMAL_PERSISTENT
        persistence_score = _clamp01(0.05 + abs(z_score) * 0.05)
        spatial_change = SpatialChangeLevel.STABLE
        spatial_change_score = _clamp01(0.05 + abs(z_score) * 0.05)
    elif 1 <= current_streak <= 6 and abs(z_score) >= 2.0:
        # Sharp new spike, only very recently started.
        persistence = PersistenceType.SUDDEN_EVENT
        persistence_score = _clamp01(0.6 + min(abs(z_score) / 10, 0.35))
        spatial_change = SpatialChangeLevel.HIGH
        spatial_change_score = _clamp01(0.6 + min(abs(z_score) / 10, 0.35))
    elif current_streak >= 10 and abs(z_score) >= 1.0:
        # An ongoing elevated pattern lasting well over a week.
        persistence = PersistenceType.ABNORMAL_PERSISTENT
        persistence_score = _clamp01(0.5 + min(abs(z_score) / 10, 0.35))
        spatial_change = SpatialChangeLevel.HIGH
        spatial_change_score = _clamp01(0.5 + min(abs(z_score) / 10, 0.35))
    elif 0.0 < recurrence_rate < 0.15 or (anomalies and current_streak < 10):
        persistence = PersistenceType.INTERMITTENT
        persistence_score = _clamp01(0.3 + min(abs(z_score) / 10, 0.25))
        spatial_change = SpatialChangeLevel.MEDIUM
        spatial_change_score = _clamp01(0.3 + min(abs(z_score) / 10, 0.25))
    else:
        persistence = PersistenceType.UNKNOWN
        persistence_score = 0.4
        spatial_change = SpatialChangeLevel.LOW
        spatial_change_score = 0.3

    return TemporalAnalysisResult(
        historical_mean=round(historical_mean, 2),
        historical_std=round(historical_std, 2),
        z_score=round(z_score, 3),
        current_deviation=round(current_deviation, 2),
        persistence=persistence,
        persistence_score=round(persistence_score, 3),
        spatial_change=spatial_change,
        spatial_change_score=round(spatial_change_score, 3),
        observations=n,
        first_observed=observations_sorted[0].obs_date,
        last_observed=observations_sorted[-1].obs_date,
        trend=trend,
        recurrence_rate=round(recurrence_rate, 3),
    )
