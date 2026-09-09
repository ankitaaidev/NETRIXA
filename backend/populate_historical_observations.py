from pathlib import Path
import math

import pandas as pd
from sqlalchemy import delete, select, func

from app.database.session import session_scope
from app.models.thermal_event import ThermalEvent
from app.models.historical_observation import HistoricalObservation


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

CURRENT_CSV = (
    BASE_DIR
    / "data"
    / "processed"
    / "thermal_events_india.csv"
)

HISTORY_CSV = (
    BASE_DIR
    / "data"
    / "processed"
    / "firms_history_india_clean.csv"
)

RADIUS_KM = 1.0


# -------------------------------------------------------------------
# Event ID
# -------------------------------------------------------------------

def build_event_id(index: int) -> str:
    return f"NTX-FIRMS-{index:06d}"


# -------------------------------------------------------------------
# Haversine distance
# -------------------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):

    earth_radius_km = 6371.0088

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * earth_radius_km * math.asin(math.sqrt(a))


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():

    # ---------------------------------------------------------------
    # Check files
    # ---------------------------------------------------------------

    if not CURRENT_CSV.exists():
        raise FileNotFoundError(
            f"Current FIRMS CSV not found: {CURRENT_CSV}"
        )

    if not HISTORY_CSV.exists():
        raise FileNotFoundError(
            f"Historical FIRMS CSV not found: {HISTORY_CSV}"
        )

    # ---------------------------------------------------------------
    # Load current events
    # ---------------------------------------------------------------

    print("Loading current FIRMS events...")

    current_df = pd.read_csv(CURRENT_CSV)

    print(f"Current events loaded: {len(current_df)}")

    # ---------------------------------------------------------------
    # Load historical FIRMS data
    # ---------------------------------------------------------------

    print()
    print("Loading historical FIRMS data...")

    history_df = pd.read_csv(HISTORY_CSV)

    print(f"Historical detections loaded: {len(history_df)}")

    # ---------------------------------------------------------------
    # Prepare datetime columns
    # ---------------------------------------------------------------

    current_df["acq_datetime"] = pd.to_datetime(
        current_df["acq_datetime"],
        errors="coerce",
    )

    current_df["acq_date"] = pd.to_datetime(
        current_df["acq_date"],
        errors="coerce",
    ).dt.date

    history_df["acq_datetime"] = pd.to_datetime(
        history_df["acq_datetime"],
        errors="coerce",
    )

    history_df["acq_date"] = pd.to_datetime(
        history_df["acq_date"],
        errors="coerce",
    ).dt.date

    # ---------------------------------------------------------------
    # Remove invalid rows
    # ---------------------------------------------------------------

    current_df = current_df.dropna(
        subset=[
            "latitude",
            "longitude",
            "brightness",
            "frp",
            "acq_datetime",
            "acq_date",
        ]
    ).copy()

    history_df = history_df.dropna(
        subset=[
            "latitude",
            "longitude",
            "bright_ti4",
            "frp",
            "acq_datetime",
            "acq_date",
        ]
    ).copy()

    # ---------------------------------------------------------------
    # Restore exact event ID mapping
    # ---------------------------------------------------------------

    current_df = current_df.reset_index(drop=True)

    current_df["event_id"] = [
        build_event_id(index + 1)
        for index in range(len(current_df))
    ]

    print()
    print("=" * 70)
    print("Historical intelligence configuration")
    print("=" * 70)
    print(f"Current events:       {len(current_df)}")
    print(f"Historical detections:{len(history_df)}")
    print(f"Search radius:        {RADIUS_KM} km")
    print(
        f"Historical period:   "
        f"{history_df['acq_date'].min()} → {history_df['acq_date'].max()}"
    )
    print("=" * 70)
    print()

    # ---------------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------------

    inserted = 0
    events_with_history = 0
    events_without_history = 0

    observation_counts = []

    # ---------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------

    with session_scope() as db:

        # -----------------------------------------------------------
        # IMPORTANT:
        # Remove the old generated historical observations first.
        #
        # We are rebuilding them from the new 36-day dataset.
        # -----------------------------------------------------------

        print("Removing old generated historical observations...")

        deleted = db.execute(
            delete(HistoricalObservation)
        )

        print(
            f"Old observations removed: {deleted.rowcount}"
        )

        # -----------------------------------------------------------
        # Process every current event
        # -----------------------------------------------------------

        for current_index, current in current_df.iterrows():

            event_id = current["event_id"]

            current_datetime = current["acq_datetime"]
            current_date = current["acq_date"]

            current_lat = float(current["latitude"])
            current_lon = float(current["longitude"])

            # -------------------------------------------------------
            # Only historical detections BEFORE the current event
            # -------------------------------------------------------

            previous = history_df[
                history_df["acq_datetime"] < current_datetime
            ]

            if previous.empty:

                observation_counts.append(0)
                events_without_history += 1
                continue

            # -------------------------------------------------------
            # Geographic filtering
            # -------------------------------------------------------

            nearby_previous = []

            for _, candidate in previous.iterrows():

                candidate_lat = float(candidate["latitude"])
                candidate_lon = float(candidate["longitude"])

                distance_km = haversine_km(
                    current_lat,
                    current_lon,
                    candidate_lat,
                    candidate_lon,
                )

                if distance_km <= RADIUS_KM:

                    nearby_previous.append(candidate)

            # -------------------------------------------------------
            # No nearby history
            # -------------------------------------------------------

            if not nearby_previous:

                observation_counts.append(0)
                events_without_history += 1
                continue

            # -------------------------------------------------------
            # Convert to DataFrame
            # -------------------------------------------------------

            nearby_df = pd.DataFrame(nearby_previous)

            # -------------------------------------------------------
            # One observation per day
            #
            # Multiple satellite detections on the same date
            # are reduced to the strongest thermal signal.
            # -------------------------------------------------------

            daily = (
                nearby_df
                .groupby("acq_date")
                .agg(
                    intensity=("bright_ti4", "max"),
                    frp=("frp", "max"),
                )
                .reset_index()
            )

            # -------------------------------------------------------
            # Never use current date as history
            # -------------------------------------------------------

            daily = daily[
                daily["acq_date"] < current_date
            ].copy()

            if daily.empty:

                observation_counts.append(0)
                events_without_history += 1
                continue

            # -------------------------------------------------------
            # Confirm event exists
            # -------------------------------------------------------

            thermal_event = db.scalar(
                select(ThermalEvent).where(
                    ThermalEvent.event_id == event_id
                )
            )

            if thermal_event is None:

                print(
                    f"WARNING: {event_id} not found in database."
                )

                observation_counts.append(0)
                events_without_history += 1
                continue

            # -------------------------------------------------------
            # Insert historical observations
            # -------------------------------------------------------

            event_observations = 0

            # -------------------------------------------------------
# Calculate historical anomalies
# -------------------------------------------------------

            historical_intensities = daily["intensity"].astype(float).tolist()

            for _, historical in daily.iterrows():

                current_intensity = float(historical["intensity"])

                # Leave-one-out baseline:
                # compare this historical day against the other
                # historical observations for the same event.
                other_values = [
                    value
                    for value in historical_intensities
                    if value != current_intensity
                ]

                if len(other_values) >= 4:
                    mean_value = sum(other_values) / len(other_values)

                    variance = (
                        sum(
                            (value - mean_value) ** 2
                            for value in other_values
                        )
                        / len(other_values)
                    )

                    std_value = math.sqrt(variance)

                    if std_value > 1e-6:
                        historical_z = (
                            current_intensity - mean_value
                        ) / std_value
                    else:
                        historical_z = 0.0
                else:
                    historical_z = 0.0

                is_anomaly = historical_z >= 2.0

                observation = HistoricalObservation(
                    event_id=event_id,
                    obs_date=historical["acq_date"],
                    intensity=current_intensity,
                    frp=float(historical["frp"]),
                    is_anomaly=is_anomaly,
                )

                db.add(observation)

                inserted += 1
                event_observations += 1

            observation_counts.append(
                event_observations
            )

            if event_observations > 0:
                events_with_history += 1
            else:
                events_without_history += 1

            # -------------------------------------------------------
            # Progress
            # -------------------------------------------------------

            if (current_index + 1) % 100 == 0:

                print(
                    f"Processed "
                    f"{current_index + 1}/"
                    f"{len(current_df)} events..."
                )

    # ---------------------------------------------------------------
    # Final statistics
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("Historical observation population completed.")
    print("=" * 70)

    print(
        f"Current FIRMS events processed: "
        f"{len(current_df)}"
    )

    print(
        f"Historical FIRMS detections used: "
        f"{len(history_df)}"
    )

    print(
        f"Events with history: "
        f"{events_with_history}"
    )

    print(
        f"Events without history: "
        f"{events_without_history}"
    )

    print(
        f"Observations inserted: "
        f"{inserted}"
    )

    print(
        f"Maximum observations/event: "
        f"{max(observation_counts, default=0)}"
    )

    print(
        f"Average observations/event: "
        f"{sum(observation_counts) / len(observation_counts):.2f}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()