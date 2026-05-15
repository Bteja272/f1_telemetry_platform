import json
from datetime import datetime

from kafka import KafkaConsumer

from app.cache.redis_client import redis_client
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import TelemetryEvent


def parse_datetime(value: str):
    if not value:
        return None

    # OpenF1 timestamps usually end with +00:00.
    # This also handles Z-style UTC timestamps.
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def create_consumer():
    return KafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="f1-telemetry-consumer-v3",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )


def save_to_database(event: dict):
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
        print("Saved to TimescaleDB")

    except Exception as e:
        db.rollback()
        print("DB insert failed:", e)

    finally:
        db.close()


def update_redis_cache(event: dict):
    redis_key = f"driver:{event['driver_number']}:latest"

    redis_client.hset(
        redis_key,
        mapping={
            "speed": event.get("speed"),
            "rpm": event.get("rpm"),
            "gear": event.get("gear"),
            "throttle": event.get("throttle"),
            "brake": event.get("brake"),
            "drs": event.get("drs"),
            "event_time": event.get("event_time"),
            "session_key": event.get("session_key"),
            "meeting_key": event.get("meeting_key"),
        },
    )

    print("Updated Redis cache")


def consume_events():
    print("Kafka telemetry consumer starting...")

    consumer = create_consumer()

    print("Kafka telemetry consumer started")

    for message in consumer:
        event = message.value

        print(
            f"Consumed telemetry: "
            f"driver={event.get('driver_number')} "
            f"speed={event.get('speed')}"
        )

        save_to_database(event)
        update_redis_cache(event)


if __name__ == "__main__":
    consume_events()