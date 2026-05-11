import json
import time
from datetime import datetime, timezone

import requests
from kafka import KafkaProducer

from app.core.config import settings


def create_kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def fetch_json(endpoint: str, params: dict | None = None) -> list[dict]:
    url = f"{settings.OPENF1_BASE_URL}/{endpoint}"
    response = requests.get(url, params=params or {}, timeout=20)

    print(f"{endpoint} URL:", response.url)
    print(f"{endpoint} status:", response.status_code)
    print(f"{endpoint} preview:", response.text[:300])

    response.raise_for_status()
    return response.json()


def get_recent_session_with_drivers() -> tuple[int, int]:
    """
    Finds a recent session and a valid driver for that session.
    This avoids hardcoding session_key/date/driver combinations.
    """
    sessions = fetch_json(
        "sessions",
        params={
            "year": 2024,
            "session_name": "Race",
        },
    )

    if not sessions:
        raise RuntimeError("No sessions found")

    # Try recent races first
    sessions = sorted(sessions, key=lambda s: s.get("date_start", ""), reverse=True)

    for session in sessions[:10]:
        session_key = session["session_key"]

        try:
            drivers = fetch_json(
                "drivers",
                params={"session_key": session_key},
            )
        except Exception:
            continue

        if drivers:
            driver_number = drivers[0]["driver_number"]
            print(f"Selected session_key={session_key}, driver_number={driver_number}")
            return session_key, driver_number

    raise RuntimeError("Could not find a session with drivers")


def fetch_openf1_car_data() -> list[dict]:
    """
    Pulls a small telemetry sample using a discovered valid session and driver.
    Uses OpenF1's CSV mode with a row limit-like strategy by filtering driver/session.
    """
    session_key, driver_number = get_recent_session_with_drivers()

    # First attempt: use only session + driver.
    # If API says too much data, we fallback to a known small limit through date discovery.
    try:
        data = fetch_json(
            "car_data",
            params={
                "session_key": session_key,
                "driver_number": driver_number,
            },
        )

        if data:
            return data[:50]

    except requests.exceptions.HTTPError as e:
        print("Initial car_data request failed; trying smaller fallback query.")

    # Fallback: discover location timestamps for same session/driver, then query near that time.
    locations = fetch_json(
        "location",
        params={
            "session_key": session_key,
            "driver_number": driver_number,
        },
    )

    if not locations:
        raise RuntimeError("No location data found for fallback")

    first_time = locations[0]["date"]

    # Query exact lower bound near known valid telemetry time.
    data = fetch_json(
        "car_data",
        params={
            "session_key": session_key,
            "driver_number": driver_number,
            "date>=": first_time,
        },
    )

    if not data:
        raise RuntimeError("No car_data found after fallback")

    return data[:50]


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
    raw_events = fetch_openf1_car_data()

    print(f"Fetched {len(raw_events)} OpenF1 telemetry events")

    for raw in raw_events[:25]:
        event = normalize_event(raw)
        producer.send(settings.KAFKA_TOPIC, value=event)
        print(
            f"Published event: "
            f"session={event['session_key']} "
            f"driver={event['driver_number']} "
            f"speed={event['speed']}"
        )
        time.sleep(0.25)

    producer.flush()
    producer.close()

    print("Finished publishing telemetry events")


if __name__ == "__main__":
    publish_events()