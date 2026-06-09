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
                "session_name": row.session_name,
                "session_type": row.session_type,
                "location": row.location,
                "country_name": row.country_name,
                "circuit_short_name": row.circuit_short_name,
                "date_start": row.date_start,
                "year": row.year,
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

        return [
            {
                "driver_number": row.driver_number,
                "full_name": row.full_name,
                "broadcast_name": row.broadcast_name,
                "name_acronym": row.name_acronym,
                "team_name": row.team_name,
                "team_colour": row.team_colour,
                "country_code": row.country_code,
                "headshot_url": row.headshot_url,
            }
            for row in rows
        ]

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
    def get_session_locations(
        self,
        db: Session,
        session_key: int,
        limit: int = 1000,
    ):
        rows = self.repository.get_session_locations(
            db=db,
            session_key=session_key,
            limit=limit,
        )

        return [
            {
                "driver_number": row.driver_number,
                "session_key": row.session_key,
                "meeting_key": row.meeting_key,
                "x": row.x,
                "y": row.y,
                "z": row.z,
                "event_time": row.event_time,
            }
            for row in rows
        ]
    def get_driver_locations_by_session(
        self,
        db: Session,
        session_key: int,
        driver_number: int,
        limit: int = 3000,
    ):
        rows = self.repository.get_driver_locations_by_session(
            db=db,
            session_key=session_key,
            driver_number=driver_number,
            limit=limit,
        )

        return [
            {
                "driver_number": row.driver_number,
                "session_key": row.session_key,
                "meeting_key": row.meeting_key,
                "x": row.x,
                "y": row.y,
                "z": row.z,
                "event_time": row.event_time,
            }
            for row in rows
        ]
    
    def get_track_map(
        self,
        db: Session,
        session_key: int,
    ):
        rows = self.repository.get_track_map(
            db=db,
            session_key=session_key,
        )

        return [
            {
                "session_key": row.session_key,
                "point_order": row.point_order,
                "x": row.x,
                "y": row.y,
                "source": row.source,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    def get_latest_locations_by_session(
        self,
        db: Session,
        session_key: int,
    ):
        rows = self.repository.get_latest_locations_by_session(
            db=db,
            session_key=session_key,
        )

        return [
            {
                "driver_number": row.driver_number,
                "session_key": row.session_key,
                "meeting_key": row.meeting_key,
                "x": row.x,
                "y": row.y,
                "z": row.z,
                "event_time": row.event_time,
            }
            for row in rows
        ]