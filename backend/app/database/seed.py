"""
Deterministic demo data generator (Phase 4).

Everything here is seeded with a fixed RNG (seed=42) so re-running produces
byte-for-byte identical data — required for DEMO_MODE to work reliably
offline and for the frontend to show stable, reproducible numbers.

This module seeds RAW data only: facilities, thermal_events, and their
historical_observations baselines. It deliberately does NOT write
event_analysis or alerts — those are genuinely computed by the real
pipeline (geospatial -> temporal -> classifier -> risk engine, Phases
5-8) in `app.services.pipeline.run_pipeline_for_all_events`, so nothing
here is a fabricated AI/risk result. Three "scenario" events are seeded
with deliberately chosen raw feature values that the pipeline is
expected to classify as described in the master plan (Scenario A/B/C);
this is verified, not assumed, by tests in tests/test_seed_scenarios.py.
"""
import random
from datetime import date, datetime, timedelta, timezone

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.seed_data.facilities_seed import FACILITIES_SEED
from app.geospatial.regions import FOREST_REGIONS, STATE_BOUNDS
from app.models.facility import Facility
from app.models.historical_observation import HistoricalObservation
from app.models.thermal_event import ThermalEvent

SEED = 42
DEMO_TODAY = date(2026, 9, 4)

SATELLITE_INSTRUMENTS = [
    ("Terra", "MODIS"),
    ("Aqua", "MODIS"),
    ("Suomi NPP", "VIIRS"),
    ("NOAA-20", "VIIRS"),
]

AGRI_STATES = ["Punjab", "Bihar", "Madhya Pradesh", "West Bengal"]

STATE_DISTRICTS = {
    "West Bengal": ["Howrah", "Hooghly", "Purba Medinipur", "Paschim Bardhaman"],
    "Gujarat": ["Jamnagar", "Surat", "Bharuch", "Vadodara"],
    "Maharashtra": ["Pune", "Nagpur", "Nashik", "Raigad"],
    "Madhya Pradesh": ["Singrauli", "Jabalpur", "Katni", "Balaghat"],
    "Odisha": ["Jagatsinghpur", "Sundargarh", "Angul", "Mayurbhanj"],
    "Manipur": ["Imphal East", "Imphal West", "Churachandpur"],
    "Bihar": ["Begusarai", "Patna", "Gaya", "Muzaffarpur"],
    "Andhra Pradesh": ["Visakhapatnam", "Krishna", "Guntur"],
    "Telangana": ["Peddapalli", "Warangal", "Karimnagar"],
    "Tamil Nadu": ["Chennai", "Cuddalore", "Coimbatore"],
    "Punjab": ["Amritsar", "Ludhiana", "Patiala", "Bathinda"],
    "Jharkhand": ["Bokaro", "Dhanbad", "Ranchi"],
    "Karnataka": ["Bellary", "Bengaluru Urban", "Belagavi"],
    "Chhattisgarh": ["Durg", "Korba", "Bilaspur"],
    "Kerala": ["Ernakulam", "Thrissur"],
    "Uttar Pradesh": ["Mathura", "Agra", "Kanpur Nagar"],
    "Haryana": ["Panipat", "Faridabad"],
    "Assam": ["Golaghat", "Dibrugarh"],
}


def _rng():
    return np.random.default_rng(SEED)


def _py_rand():
    r = random.Random(SEED)
    return r


def jitter(rng, lat, lon, max_deg=0.05):
    return lat + rng.uniform(-max_deg, max_deg), lon + rng.uniform(-max_deg, max_deg)


def random_point_in_state(rng, state):
    lat_min, lat_max, lon_min, lon_max = STATE_BOUNDS[state]
    return rng.uniform(lat_min, lat_max), rng.uniform(lon_min, lon_max)


def random_detection_time(rng, days_back_max=180):
    days_back = int(rng.uniform(0, days_back_max))
    seconds = int(rng.uniform(0, 86400))
    dt = datetime(DEMO_TODAY.year, DEMO_TODAY.month, DEMO_TODAY.day, tzinfo=timezone.utc) - timedelta(
        days=days_back, seconds=-seconds
    )
    return dt


def seed_facilities(db: Session) -> list[Facility]:
    existing = db.execute(select(Facility.facility_id)).scalars().all()
    if existing:
        return db.execute(select(Facility)).scalars().all()

    facilities = []
    for facility_id, name, facility_type, category, lat, lon, state, district in FACILITIES_SEED:
        fac = Facility(
            facility_id=facility_id,
            name=name,
            facility_type=facility_type,
            facility_category=category,
            latitude=lat,
            longitude=lon,
            state=state,
            district=district,
            source="DEMO",
        )
        db.add(fac)
        facilities.append(fac)
    db.flush()
    return facilities


class EventSpec:
    """Intermediate representation before DB insert, carries the intended
    category label so tests/calibration can check the pipeline agrees."""

    def __init__(self, event_id, lat, lon, detection_time, brightness_temperature, frp, confidence,
                 satellite, instrument, state, district, land_cover, category, baseline_mean, baseline_std,
                 is_anomaly_recent, near_facility=None, anomaly_tail_days=3):
        self.event_id = event_id
        self.lat = lat
        self.lon = lon
        self.detection_time = detection_time
        self.brightness_temperature = brightness_temperature
        self.frp = frp
        self.confidence = confidence
        self.satellite = satellite
        self.instrument = instrument
        self.state = state
        self.district = district
        self.land_cover = land_cover
        self.category = category  # intended classification, for calibration/testing only
        self.baseline_mean = baseline_mean
        self.baseline_std = baseline_std
        self.is_anomaly_recent = is_anomaly_recent
        self.near_facility = near_facility  # facility_id, for scenario/testing convenience
        # How many of the most recent days show the anomalous spike.
        # A short tail (~3 days) reads as a fresh SUDDEN_EVENT; a longer
        # tail (~15-20 days) reads as an ongoing ABNORMAL_PERSISTENT
        # pattern — see temporal_service's recurrence/recency logic.
        self.anomaly_tail_days = anomaly_tail_days


def _next_id_factory():
    counters = {"IND": 0, "WLD": 0}

    def next_id(prefix="IND"):
        counters[prefix] += 1
        return f"NTX-{prefix}-{counters[prefix]:05d}"

    return next_id


def generate_event_specs(facilities: list[Facility]) -> list[EventSpec]:
    rng = _rng()
    py_rng = _py_rand()
    next_id = _next_id_factory()
    specs: list[EventSpec] = []

    fac_by_id = {f.facility_id: f for f in facilities}

    def pick_satellite():
        return SATELLITE_INSTRUMENTS[int(rng.uniform(0, len(SATELLITE_INSTRUMENTS)))]

    # ---- Named Scenario A: normal refinery thermal activity (persistent, LOW risk) ----
    fac_a = fac_by_id["FAC-002"]  # Hazira LNG Terminal
    lat, lon = jitter(rng, fac_a.latitude, fac_a.longitude, max_deg=0.003)
    sat, inst = pick_satellite()
    specs.append(EventSpec(
        event_id=next_id("IND"), lat=lat, lon=lon,
        detection_time=random_detection_time(rng, days_back_max=5),
        brightness_temperature=352.0, frp=38.0, confidence=88.0,
        satellite=sat, instrument=inst, state=fac_a.state, district=fac_a.district,
        land_cover="Industrial", category="Persistent Industrial Thermal Source",
        baseline_mean=350.0, baseline_std=6.0, is_anomaly_recent=False, near_facility=fac_a.facility_id,
    ))

    # ---- Named Scenario B: agricultural hotspot (LOW risk, no action) ----
    lat, lon = random_point_in_state(rng, "Punjab")
    sat, inst = pick_satellite()
    specs.append(EventSpec(
        event_id=next_id("IND"), lat=lat, lon=lon,
        detection_time=random_detection_time(rng, days_back_max=10),
        brightness_temperature=330.0, frp=18.0, confidence=76.0,
        satellite=sat, instrument=inst, state="Punjab", district="Amritsar",
        land_cover="Cropland", category="Agricultural Burning",
        baseline_mean=305.0, baseline_std=10.0, is_anomaly_recent=False, near_facility=None,
    ))

    # ---- Named Scenario C: abnormal industrial thermal event (CRITICAL risk) ----
    fac_c = fac_by_id["FAC-001"]  # Jamnagar Refinery
    lat, lon = jitter(rng, fac_c.latitude, fac_c.longitude, max_deg=0.003)
    sat, inst = pick_satellite()
    specs.append(EventSpec(
        event_id=next_id("IND"), lat=lat, lon=lon,
        detection_time=random_detection_time(rng, days_back_max=1),
        brightness_temperature=418.0, frp=165.0, confidence=94.0,
        satellite=sat, instrument=inst, state=fac_c.state, district=fac_c.district,
        land_cover="Industrial", category="Potential Industrial Fire",
        baseline_mean=345.0, baseline_std=8.0, is_anomaly_recent=True, near_facility=fac_c.facility_id,
    ))

    # ---- Persistent Industrial Thermal Sources (14 more, total 15) ----
    industrial_facs = [f for f in facilities if f.facility_category in
                        ("refinery", "petrochemical", "thermal_power", "steel")]
    for i in range(14):
        fac = industrial_facs[i % len(industrial_facs)]
        lat, lon = jitter(rng, fac.latitude, fac.longitude, max_deg=0.004)
        sat, inst = pick_satellite()
        base_temp = float(rng.uniform(338, 362))
        specs.append(EventSpec(
            event_id=next_id("IND"), lat=lat, lon=lon,
            detection_time=random_detection_time(rng, days_back_max=90),
            brightness_temperature=base_temp + float(rng.uniform(-2, 2)), frp=float(rng.uniform(20, 90)),
            confidence=float(rng.uniform(75, 95)),
            satellite=sat, instrument=inst, state=fac.state, district=fac.district,
            land_cover="Industrial", category="Persistent Industrial Thermal Source",
            baseline_mean=base_temp, baseline_std=float(rng.uniform(3, 8)), is_anomaly_recent=False,
            near_facility=fac.facility_id,
        ))

    # ---- Gas Flares (15) ----
    flare_facs = [f for f in facilities if f.facility_category in ("refinery", "lng", "petrochemical")]
    for i in range(15):
        fac = flare_facs[i % len(flare_facs)]
        lat, lon = jitter(rng, fac.latitude, fac.longitude, max_deg=0.004)
        sat, inst = pick_satellite()
        base_temp = float(rng.uniform(365, 400))
        specs.append(EventSpec(
            event_id=next_id("IND"), lat=lat, lon=lon,
            detection_time=random_detection_time(rng, days_back_max=90),
            brightness_temperature=base_temp + float(rng.uniform(-3, 3)), frp=float(rng.uniform(10, 35)),
            confidence=float(rng.uniform(80, 97)),
            satellite=sat, instrument=inst, state=fac.state, district=fac.district,
            land_cover="Industrial", category="Gas Flare",
            baseline_mean=base_temp, baseline_std=float(rng.uniform(2, 5)), is_anomaly_recent=False,
            near_facility=fac.facility_id,
        ))

    # ---- Agricultural Burning (89 more, total 90) ----
    for i in range(89):
        state = AGRI_STATES[i % len(AGRI_STATES)]
        lat, lon = random_point_in_state(rng, state)
        sat, inst = pick_satellite()
        district = STATE_DISTRICTS[state][int(rng.uniform(0, len(STATE_DISTRICTS[state])))]
        base_temp = float(rng.uniform(295, 315))
        specs.append(EventSpec(
            event_id=next_id("IND"), lat=lat, lon=lon,
            detection_time=random_detection_time(rng, days_back_max=60),
            brightness_temperature=float(rng.uniform(318, 345)), frp=float(rng.uniform(5, 40)),
            confidence=float(rng.uniform(60, 85)),
            satellite=sat, instrument=inst, state=state, district=district,
            land_cover="Cropland", category="Agricultural Burning",
            baseline_mean=base_temp, baseline_std=float(rng.uniform(8, 14)), is_anomaly_recent=False,
            near_facility=None,
        ))

    # ---- Wildfire (25) ----
    for i in range(25):
        region = FOREST_REGIONS[i % len(FOREST_REGIONS)]
        state, base_lat, base_lon, district = region
        lat, lon = jitter(rng, base_lat, base_lon, max_deg=0.6)
        sat, inst = pick_satellite()
        specs.append(EventSpec(
            event_id=next_id("WLD"), lat=lat, lon=lon,
            detection_time=random_detection_time(rng, days_back_max=120),
            brightness_temperature=float(rng.uniform(330, 362)), frp=float(rng.uniform(15, 65)),
            confidence=float(rng.uniform(70, 92)),
            satellite=sat, instrument=inst, state=state, district=district,
            land_cover="Forest", category="Wildfire",
            baseline_mean=float(rng.uniform(295, 305)), baseline_std=float(rng.uniform(4, 9)),
            is_anomaly_recent=True, near_facility=None,
        ))

    # ---- Mining Activity (20) ----
    mining_facs = [f for f in facilities if f.facility_category == "mining"]
    for i in range(20):
        fac = mining_facs[i % len(mining_facs)]
        lat, lon = jitter(rng, fac.latitude, fac.longitude, max_deg=0.08)
        sat, inst = pick_satellite()
        base_temp = float(rng.uniform(305, 325))
        specs.append(EventSpec(
            event_id=next_id("IND"), lat=lat, lon=lon,
            detection_time=random_detection_time(rng, days_back_max=90),
            brightness_temperature=base_temp + float(rng.uniform(-3, 5)), frp=float(rng.uniform(5, 25)),
            confidence=float(rng.uniform(55, 80)),
            satellite=sat, instrument=inst, state=fac.state, district=fac.district,
            land_cover="Barren/Mining", category="Mining Activity",
            baseline_mean=base_temp, baseline_std=float(rng.uniform(4, 9)), is_anomaly_recent=False,
            near_facility=fac.facility_id,
        ))

    # ---- Unknown / Insufficient Evidence (30) ----
    all_states = list(STATE_BOUNDS.keys())
    for i in range(30):
        state = all_states[i % len(all_states)]
        lat, lon = random_point_in_state(rng, state)
        sat, inst = pick_satellite()
        district = STATE_DISTRICTS[state][int(rng.uniform(0, len(STATE_DISTRICTS[state])))]
        specs.append(EventSpec(
            event_id=next_id("IND"), lat=lat, lon=lon,
            detection_time=random_detection_time(rng, days_back_max=150),
            brightness_temperature=float(rng.uniform(300, 340)), frp=float(rng.uniform(3, 30)),
            confidence=float(rng.uniform(40, 65)),
            satellite=sat, instrument=inst, state=state, district=district,
            land_cover="Mixed/Unclassified", category="Unknown / Insufficient Evidence",
            baseline_mean=float(rng.uniform(300, 320)), baseline_std=float(rng.uniform(6, 14)),
            is_anomaly_recent=False, near_facility=None,
        ))

    # ---- Potential Industrial Fire / Industrial Fire anomalies (11 more, total 12) ----
    # At least 5 must reach CRITICAL severity by construction: large temp/FRP spike
    # far above baseline. We mark the first 6 as "severe" (-> CRITICAL expected),
    # remaining 5 as moderate (-> HIGH expected).
    anomaly_facs = [f for f in facilities if f.facility_category in ("refinery", "petrochemical", "steel", "thermal_power")]
    for i in range(11):
        fac = anomaly_facs[i % len(anomaly_facs)]
        lat, lon = jitter(rng, fac.latitude, fac.longitude, max_deg=0.004)
        sat, inst = pick_satellite()
        severe = i < 6
        base_temp = float(rng.uniform(335, 350))
        spike = float(rng.uniform(55, 90)) if severe else float(rng.uniform(25, 45))
        frp = float(rng.uniform(120, 220)) if severe else float(rng.uniform(60, 110))
        classification = "Potential Industrial Fire" if severe else "Industrial Fire"
        specs.append(EventSpec(
            event_id=next_id("IND"), lat=lat, lon=lon,
            detection_time=random_detection_time(rng, days_back_max=14),
            brightness_temperature=base_temp + spike, frp=frp,
            confidence=float(rng.uniform(85, 98)),
            satellite=sat, instrument=inst, state=fac.state, district=fac.district,
            land_cover="Industrial", category=classification,
            baseline_mean=base_temp, baseline_std=float(rng.uniform(5, 9)), is_anomaly_recent=True,
            near_facility=fac.facility_id,
            # Severe ("Potential Industrial Fire") = fresh spike, last 3 days only.
            # Moderate ("Industrial Fire") = an ongoing pattern over the last ~18
            # days, so temporal_service reads it as ABNORMAL_PERSISTENT rather
            # than SUDDEN_EVENT.
            anomaly_tail_days=3 if severe else 18,
        ))

    return specs


def seed_historical_observations(db: Session, event: ThermalEvent, spec: EventSpec, n_days: int = 90) -> None:
    rng = np.random.default_rng(abs(hash(event.event_id)) % (2**32))
    existing = db.execute(
        select(HistoricalObservation.id).where(HistoricalObservation.event_id == event.event_id)
    ).first()
    if existing:
        return

    for d in range(n_days):
        obs_date = DEMO_TODAY - timedelta(days=(n_days - d))
        is_anomaly = spec.is_anomaly_recent and d >= n_days - spec.anomaly_tail_days
        if is_anomaly:
            intensity = spec.brightness_temperature + float(rng.uniform(-2, 2))
            frp = spec.frp + float(rng.uniform(-5, 5))
        else:
            intensity = spec.baseline_mean + float(rng.normal(0, spec.baseline_std))
            frp = max(1.0, spec.frp * 0.3 + float(rng.normal(0, spec.baseline_std)))
        db.add(HistoricalObservation(
            event_id=event.event_id, obs_date=obs_date, intensity=round(intensity, 2),
            frp=round(frp, 2), is_anomaly=is_anomaly,
        ))


def seed_thermal_events(db: Session, facilities: list[Facility]) -> list[tuple[ThermalEvent, EventSpec]]:
    existing = db.execute(select(ThermalEvent.event_id)).scalars().all()
    if existing:
        events = db.execute(select(ThermalEvent)).scalars().all()
        # We don't have specs for pre-existing rows on a second run; historical
        # obs seeding is skipped in that case (idempotency handles re-runs).
        return [(e, None) for e in events]

    specs = generate_event_specs(facilities)
    pairs = []
    for spec in specs:
        evt = ThermalEvent(
            event_id=spec.event_id,
            latitude=round(spec.lat, 5),
            longitude=round(spec.lon, 5),
            detection_time=spec.detection_time,
            brightness_temperature=round(spec.brightness_temperature, 2),
            frp=round(spec.frp, 2),
            confidence=round(spec.confidence, 1),
            satellite=spec.satellite,
            instrument=spec.instrument,
            source="DEMO",
            state=spec.state,
            district=spec.district,
            land_cover=spec.land_cover,
        )
        db.add(evt)
        pairs.append((evt, spec))
    db.flush()

    for evt, spec in pairs:
        seed_historical_observations(db, evt, spec)
    db.flush()

    return pairs


def seed_all(db: Session) -> dict:
    facilities = seed_facilities(db)
    pairs = seed_thermal_events(db, facilities)
    db.commit()
    return {
        "facilities": len(facilities),
        "thermal_events": len(pairs),
    }


if __name__ == "__main__":
    from app.database.init_db import init_db
    from app.database.session import get_session_factory

    init_db()
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        result = seed_all(session)
        print(f"Seeded: {result}")
    finally:
        session.close()
