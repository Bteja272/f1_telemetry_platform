import json
import time
from datetime import datetime, timezone

import requests
from kafka import KafkaProducer
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import DriverMetadata
from app.db.models import SessionMetadata


MAX_DRIVERS = None
EVENTS_PER_DRIVER = 40
LOCATION_EVENTS_PER_DRIVER = 80
MIN_SPEED = 100


def create_kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def parse_datetime(value: str | None):
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_json(endpoint: str, params: dict | None = None) -> list[dict]:
    url = f"{settings.OPENF1_BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        params=params or {},
        timeout=20,
    )

    print(f"{endpoint} URL:", response.url)
    print(f"{endpoint} status:", response.status_code)
    print(f"{endpoint} preview:", response.text[:300])

    response.raise_for_status()

    return response.json()


def save_session_metadata(session: dict):
    db = SessionLocal()

    try:
        statement = insert(SessionMetadata).values(
            session_key=session.get("session_key"),
            meeting_key=session.get("meeting_key"),
            session_name=session.get("session_name"),
            session_type=session.get("session_type"),
            date_start=parse_datetime(session.get("date_start")),
            date_end=parse_datetime(session.get("date_end")),
            location=session.get("location"),
            country_name=session.get("country_name"),
            circuit_short_name=session.get("circuit_short_name"),
            year=parse_datetime(session.get("date_start")).year
            if session.get("date_start")
            else None,
        )

        update_values = {
            "meeting_key": statement.excluded.meeting_key,
            "session_name": statement.excluded.session_name,
            "session_type": statement.excluded.session_type,
            "date_start": statement.excluded.date_start,
            "date_end": statement.excluded.date_end,
            "location": statement.excluded.location,
            "country_name": statement.excluded.country_name,
            "circuit_short_name": statement.excluded.circuit_short_name,
            "year": statement.excluded.year,
        }

        statement = statement.on_conflict_do_update(
            index_elements=["session_key"],
            set_=update_values,
        )

        db.execute(statement)
        db.commit()

        print(
            f"Saved session metadata: "
            f"{session.get('location')} - {session.get('date_start')}"
        )

    except Exception as error:
        db.rollback()
        print("Failed to save session metadata:", error)

    finally:
        db.close()


def save_driver_metadata(session_key: int, driver: dict):
    db = SessionLocal()

    try:
        statement = insert(DriverMetadata).values(
            driver_number=driver.get("driver_number"),
            session_key=session_key,
            full_name=driver.get("full_name"),
            broadcast_name=driver.get("broadcast_name"),
            name_acronym=driver.get("name_acronym"),
            team_name=driver.get("team_name"),
            team_colour=driver.get("team_colour"),
            first_name=driver.get("first_name"),
            last_name=driver.get("last_name"),
            country_code=driver.get("country_code"),
            headshot_url=driver.get("headshot_url"),
        )

        update_values = {
            "full_name": statement.excluded.full_name,
            "broadcast_name": statement.excluded.broadcast_name,
            "name_acronym": statement.excluded.name_acronym,
            "team_name": statement.excluded.team_name,
            "team_colour": statement.excluded.team_colour,
            "first_name": statement.excluded.first_name,
            "last_name": statement.excluded.last_name,
            "country_code": statement.excluded.country_code,
            "headshot_url": statement.excluded.headshot_url,
        }

        statement = statement.on_conflict_do_update(
            index_elements=["driver_number", "session_key"],
            set_=update_values,
        )

        db.execute(statement)
        db.commit()

        print(
            f"Saved driver metadata: "
            f"{driver.get('name_acronym')} - {driver.get('full_name')}"
        )

    except Exception as error:
        db.rollback()
        print("Failed to save driver metadata:", error)

    finally:
        db.close()


def get_recent_race_session() -> dict:
    sessions = fetch_json(
        "sessions",
        params={
            "year": 2024,
            "session_name": "Race",
        },
    )

    if not sessions:
        raise RuntimeError("No race sessions found")

    sessions = sorted(
        sessions,
        key=lambda session: session.get("date_start", ""),
        reverse=True,
    )

    selected_session = sessions[0]

    print(
        f"Selected session_key={selected_session.get('session_key')}, "
        f"location={selected_session.get('location')}, "
        f"country={selected_session.get('country_name')}, "
        f"date={selected_session.get('date_start')}"
    )

    save_session_metadata(selected_session)

    return selected_session


def get_drivers_for_session(session_key: int) -> list[dict]:
    drivers = fetch_json(
        "drivers",
        params={"session_key": session_key},
    )

    if not drivers:
        raise RuntimeError(f"No drivers found for session_key={session_key}")

    valid_drivers = [
        driver
        for driver in drivers
        if driver.get("driver_number") is not None
    ]

    selected_drivers = (
        valid_drivers
        if MAX_DRIVERS is None
        else valid_drivers[:MAX_DRIVERS]
    )

    for driver in selected_drivers:
        save_driver_metadata(
            session_key=session_key,
            driver=driver,
        )

    print(f"Found {len(valid_drivers)} drivers for session {session_key}")
    print(
        "Using drivers:",
        [
            {
                "driver_number": driver.get("driver_number"),
                "name": driver.get("full_name"),
                "team": driver.get("team_name"),
            }
            for driver in selected_drivers
        ],
    )

    return selected_drivers


def fetch_driver_car_data(
    session_key: int,
    driver_number: int,
) -> list[dict]:
    try:
        data = fetch_json(
            "car_data",
            params={
                "session_key": session_key,
                "driver_number": driver_number,
                "speed>": MIN_SPEED,
            },
        )

    except requests.exceptions.HTTPError as error:
        print(
            f"Skipping telemetry for driver={driver_number}. "
            f"OpenF1 request failed: {error}"
        )
        return []

    if not data:
        print(f"No moving telemetry found for driver={driver_number}")
        return []

    return data[:EVENTS_PER_DRIVER]


def fetch_driver_location_data(
    session_key: int,
    driver_number: int,
) -> list[dict]:
    try:
        data = fetch_json(
            "location",
            params={
                "session_key": session_key,
                "driver_number": driver_number,
            },
        )

    except requests.exceptions.HTTPError as error:
        print(
            f"Skipping location data for driver={driver_number}. "
            f"OpenF1 request failed: {error}"
        )
        return []

    if not data:
        print(f"No location data found for driver={driver_number}")
        return []

    valid_locations = [
    row for row in data
    if row.get("x") not in (None, 0)
    and row.get("y") not in (None, 0)
]

    if not valid_locations:
        print(f"No non-zero location data found for driver={driver_number}")
        return []

    return valid_locations[:LOCATION_EVENTS_PER_DRIVER]


def normalize_telemetry_event(raw: dict) -> dict:
    return {
        "event_type": "telemetry",
        "driver_number": raw.get("driver_number"),
        "session_key": raw.get("session_key"),
        "meeting_key": raw.get("meeting_key"),
        "speed": raw.get("speed"),
        "rpm": raw.get("rpm"),
        "gear": raw.get("n_gear"),
        "throttle": raw.get("throttle"),
        "brake": raw.get("brake"),
        "drs": raw.get("drs"),
        "event_time": raw.get("date"),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def normalize_location_event(raw: dict) -> dict:
    return {
        "event_type": "location",
        "driver_number": raw.get("driver_number"),
        "session_key": raw.get("session_key"),
        "meeting_key": raw.get("meeting_key"),
        "x": raw.get("x"),
        "y": raw.get("y"),
        "z": raw.get("z"),
        "event_time": raw.get("date"),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def publish_events():
    producer = create_kafka_producer()

    session = get_recent_race_session()
    session_key = session["session_key"]

    drivers = get_drivers_for_session(session_key)

    total_telemetry_published = 0
    total_location_published = 0

    for driver in drivers:
        driver_number = driver["driver_number"]

        raw_events = fetch_driver_car_data(
            session_key=session_key,
            driver_number=driver_number,
        )

        print(
            f"Fetched {len(raw_events)} moving telemetry events "
            f"for driver={driver_number} ({driver.get('full_name')})"
        )

        for raw in raw_events:
            event = normalize_telemetry_event(raw)

            producer.send(
                settings.KAFKA_TOPIC,
                value=event,
            )

            total_telemetry_published += 1

            print(
                f"Published telemetry: "
                f"driver={event['driver_number']} "
                f"speed={event['speed']} "
                f"rpm={event['rpm']} "
                f"gear={event['gear']}"
            )

            time.sleep(0.05)

        raw_locations = fetch_driver_location_data(
            session_key=session_key,
            driver_number=driver_number,
        )

        print(
            f"Fetched {len(raw_locations)} location events "
            f"for driver={driver_number} ({driver.get('full_name')})"
        )

        for raw_location in raw_locations:
            location_event = normalize_location_event(raw_location)

            producer.send(
                settings.KAFKA_TOPIC,
                value=location_event,
            )

            total_location_published += 1

            print(
                f"Published location: "
                f"driver={location_event['driver_number']} "
                f"x={location_event['x']} "
                f"y={location_event['y']}"
            )

            time.sleep(0.02)

    producer.flush()
    producer.close()

    print(
        f"Finished publishing "
        f"{total_telemetry_published} telemetry events and "
        f"{total_location_published} location events"
    )


if __name__ == "__main__":
    publish_events()