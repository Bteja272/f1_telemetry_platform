from sqlalchemy.orm import Session

from app.cache.redis_client import redis_client
from app.repositories.telemetry_repository import TelemetryRepository


class TelemetryService:
    def __init__(self):
        self.repository = TelemetryRepository()

    def get_latest_driver_state(self, driver_number: int):
        redis_key = f"driver:{driver_number}:latest"
        data = redis_client.hgetall(redis_key)

        if not data:
            return None

        return {
            "driver_number": driver_number,
            "speed": float(data.get("speed", 0)),
            "rpm": int(data.get("rpm", 0)),
            "gear": int(data.get("gear", 0)),
            "throttle": float(data.get("throttle", 0)),
            "brake": float(data.get("brake", 0)),
            "drs": int(data.get("drs", 0)),
            "event_time": data.get("event_time"),
            "session_key": int(data.get("session_key", 0)),
            "meeting_key": int(data.get("meeting_key", 0)),
        }

    def get_driver_history(
        self,
        db: Session,
        driver_number: int,
        limit: int = 100,
    ):
        rows = self.repository.get_driver_history(
            db=db,
            driver_number=driver_number,
            limit=limit,
        )

        return self._format_telemetry_rows(rows)

    def get_driver_history_by_session(
        self,
        db: Session,
        driver_number: int,
        session_key: int,
        limit: int = 100,
    ):
        rows = self.repository.get_driver_history_by_session(
            db=db,
            driver_number=driver_number,
            session_key=session_key,
            limit=limit,
        )

        return self._format_telemetry_rows(rows)

    def get_available_sessions(self, db: Session):
        rows = self.repository.get_available_sessions(db)

        return [
            {
                "session_key": row.session_key,
                "meeting_key": row.meeting_key,
            }
            for row in rows
        ]

    def get_drivers_by_session(
        self,
        db: Session,
        session_key: int,
    ):
        rows = self.repository.get_drivers_by_session(
            db=db,
            session_key=session_key,
        )

        return [row.driver_number for row in rows]

    def get_metrics(self, db: Session):
        total_events = self.repository.count_events(db)
        distinct_drivers = self.repository.count_distinct_drivers(db)

        return {
            "total_telemetry_events": total_events,
            "distinct_drivers": distinct_drivers,
        }

    def _format_telemetry_rows(self, rows):
        return [
            {
                "driver_number": row.driver_number,
                "speed": row.speed,
                "rpm": row.rpm,
                "gear": row.gear,
                "throttle": row.throttle,
                "brake": row.brake,
                "drs": row.drs,
                "event_time": row.event_time,
                "session_key": row.session_key,
                "meeting_key": row.meeting_key,
            }
            for row in rows
        ]