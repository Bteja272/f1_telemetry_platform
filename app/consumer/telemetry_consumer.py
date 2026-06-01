import json
from datetime import datetime

from kafka import KafkaConsumer
from sqlalchemy.exc import IntegrityError

from app.cache.redis_client import redis_client
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import LocationEvent
from app.db.models import TelemetryEvent


def parse_datetime(value: str):
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def create_consumer():
    return KafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="f1-telemetry-consumer-v5",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )


def save_telemetry_to_database(event: dict):
    db = SessionLocal()

    try:
        telemetry_event = TelemetryEvent(
            event_time=parse_datetime(event["event_time"]),
            ingested_at=parse_datetime(event["ingested_at"]),
            meeting_key=event.get("meeting_key"),
            session_key=event.get("session_key"),
            driver_number=event["driver_number"],
            speed=event.get("speed"),
            rpm=event.get("rpm"),
            gear=event.get("gear"),
            throttle=event.get("throttle"),
            brake=event.get("brake"),
            drs=event.get("drs"),
        )

        db.add(telemetry_event)
        db.commit()
        print("Saved telemetry to TimescaleDB")

    except IntegrityError:
        db.rollback()
        print("Duplicate telemetry event skipped")

    except Exception as e:
        db.rollback()
        print("Telemetry DB insert failed:", e)

    finally:
        db.close()


def save_location_to_database(event: dict):
    db = SessionLocal()

    try:
        location_event = LocationEvent(
            event_time=parse_datetime(event["event_time"]),
            ingested_at=parse_datetime(event["ingested_at"]),
            meeting_key=event.get("meeting_key"),
            session_key=event.get("session_key"),
            driver_number=event["driver_number"],
            x=event.get("x"),
            y=event.get("y"),
            z=event.get("z"),
        )

        db.add(location_event)
        db.commit()
        print("Saved location to TimescaleDB")

    except IntegrityError:
        db.rollback()
        print("Duplicate location event skipped")

    except Exception as e:
        db.rollback()
        print("Location DB insert failed:", e)

    finally:
        db.close()


def update_telemetry_redis_cache(event: dict):
    redis_key = f"driver:{event['driver_number']}:latest"

    redis_client.hset(
        redis_key,
        mapping={
            "speed": event.get("speed", 0),
            "rpm": event.get("rpm", 0),
            "gear": event.get("gear", 0),
            "throttle": event.get("throttle", 0),
            "brake": event.get("brake", 0),
            "drs": event.get("drs", 0),
            "event_time": event.get("event_time", ""),
            "session_key": event.get("session_key", ""),
            "meeting_key": event.get("meeting_key", ""),
        },
    )

    print(
        f"Updated telemetry cache: "
        f"driver={event.get('driver_number')} "
        f"speed={event.get('speed')} "
        f"rpm={event.get('rpm')}"
    )


def update_location_redis_cache(event: dict):
    redis_key = f"driver:{event['driver_number']}:location"

    redis_client.hset(
        redis_key,
        mapping={
            "x": event.get("x", 0),
            "y": event.get("y", 0),
            "z": event.get("z", 0),
            "event_time": event.get("event_time", ""),
            "session_key": event.get("session_key", ""),
            "meeting_key": event.get("meeting_key", ""),
        },
    )

    print(
        f"Updated location cache: "
        f"driver={event.get('driver_number')} "
        f"x={event.get('x')} "
        f"y={event.get('y')}"
    )


def consume_events():
    print("Kafka telemetry/location consumer starting...")

    consumer = create_consumer()

    print("Kafka telemetry/location consumer started")

    for message in consumer:
        event = message.value
        event_type = event.get("event_type", "telemetry")

        if event_type == "location":
            print(
                f"Consumed location: "
                f"driver={event.get('driver_number')} "
                f"x={event.get('x')} "
                f"y={event.get('y')}"
            )

            save_location_to_database(event)
            update_location_redis_cache(event)

        else:
            print(
                f"Consumed telemetry: "
                f"driver={event.get('driver_number')} "
                f"speed={event.get('speed')} "
                f"rpm={event.get('rpm')}"
            )

            save_telemetry_to_database(event)
            update_telemetry_redis_cache(event)


if __name__ == "__main__":
    consume_events()