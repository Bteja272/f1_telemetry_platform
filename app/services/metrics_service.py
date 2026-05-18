import time

from sqlalchemy.orm import Session

from app.cache.redis_client import redis_client
from app.db.models import TelemetryEvent


class MetricsService:
    def get_system_metrics(self, db: Session):
        metrics = {}

        db_start = time.perf_counter()

        total_events = db.query(TelemetryEvent).count()

        latest_event = (
            db.query(TelemetryEvent)
            .order_by(TelemetryEvent.event_time.desc())
            .first()
        )

        db_latency_ms = round((time.perf_counter() - db_start) * 1000, 2)

        redis_start = time.perf_counter()

        redis_keys = redis_client.keys("driver:*:latest")

        redis_latency_ms = round((time.perf_counter() - redis_start) * 1000, 2)

        metrics["total_telemetry_events"] = total_events
        metrics["active_cached_drivers"] = len(redis_keys)
        metrics["latest_event_time"] = latest_event.event_time if latest_event else None
        metrics["latest_driver_number"] = latest_event.driver_number if latest_event else None
        metrics["timescaledb_query_latency_ms"] = db_latency_ms
        metrics["redis_query_latency_ms"] = redis_latency_ms

        return metrics