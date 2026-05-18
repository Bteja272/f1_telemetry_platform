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


def get_recent_session_with_drivers() -> tuple[int, int]:
    sessions = fetch_json(
        "sessions",
        params={
            "year": 2024,
            "session_name": "Race",
        },
    )

    if not sessions:
        raise RuntimeError("No sessions found")

    sessions = sorted(
        sessions,
        key=lambda s: s.get("date_start", ""),
        reverse=True,
    )

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

            print(
                f"Selected session_key={session_key}, "
                f"driver_number={driver_number}"
            )

            return session_key, driver_number

    raise RuntimeError("Could not find a valid session")


def fetch_openf1_car_data() -> list[dict]:
    session_key, driver_number = get_recent_session_with_drivers()

    data = fetch_json(
        "car_data",
        params={
            "session_key": session_key,
            "driver_number": driver_number,
            "speed>": 100,
        },
    )

    if not data:
        raise RuntimeError("No moving telemetry found")

    return data[:100]


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

    print(f"Fetched {len(raw_events)} moving telemetry events")

    for raw in raw_events:
        event = normalize_event(raw)

        producer.send(
            settings.KAFKA_TOPIC,
            value=event,
        )

        print(
            f"Published: "
            f"driver={event['driver_number']} "
            f"speed={event['speed']} "
            f"rpm={event['rpm']} "
            f"gear={event['gear']}"
        )

        time.sleep(0.15)

    producer.flush()
    producer.close()

    print("Finished publishing telemetry events")


if __name__ == "__main__":
    publish_events()