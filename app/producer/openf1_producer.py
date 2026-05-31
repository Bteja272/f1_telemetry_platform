import json
import time
from datetime import datetime, timezone

import requests
from kafka import KafkaProducer

from app.core.config import settings


MAX_DRIVERS = 8
EVENTS_PER_DRIVER = 40
MIN_SPEED = 100


def create_kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


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


def get_recent_race_session() -> int:
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
    session_key = selected_session["session_key"]

    print(
        f"Selected session_key={session_key}, "
        f"location={selected_session.get('location')}, "
        f"country={selected_session.get('country_name')}"
    )

    return session_key


def get_drivers_for_session(session_key: int) -> list[int]:
    drivers = fetch_json(
        "drivers",
        params={"session_key": session_key},
    )

    if not drivers:
        raise RuntimeError(f"No drivers found for session_key={session_key}")

    driver_numbers = [
        driver["driver_number"]
        for driver in drivers
        if driver.get("driver_number") is not None
    ]

    print(f"Found {len(driver_numbers)} drivers for session {session_key}")
    print(f"Using drivers: {driver_numbers[:MAX_DRIVERS]}")

    return driver_numbers[:MAX_DRIVERS]


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
            f"Skipping driver={driver_number}. "
            f"OpenF1 request failed: {error}"
        )
        return []

    if not data:
        print(f"No moving telemetry found for driver={driver_number}")
        return []

    return data[:EVENTS_PER_DRIVER]


def normalize_event(raw: dict) -> dict:
    return {
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


def publish_events():
    producer = create_kafka_producer()

    session_key = get_recent_race_session()
    driver_numbers = get_drivers_for_session(session_key)

    total_published = 0

    for driver_number in driver_numbers:
        raw_events = fetch_driver_car_data(
            session_key=session_key,
            driver_number=driver_number,
        )

        print(
            f"Fetched {len(raw_events)} moving telemetry events "
            f"for driver={driver_number}"
        )

        for raw in raw_events:
            event = normalize_event(raw)

            producer.send(
                settings.KAFKA_TOPIC,
                value=event,
            )

            total_published += 1

            print(
                f"Published: "
                f"driver={event['driver_number']} "
                f"speed={event['speed']} "
                f"rpm={event['rpm']} "
                f"gear={event['gear']}"
            )

            time.sleep(0.05)

    producer.flush()
    producer.close()

    print(f"Finished publishing {total_published} telemetry events")


if __name__ == "__main__":
    publish_events()