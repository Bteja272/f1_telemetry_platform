from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import DriverMetadata
from app.db.models import SessionMetadata
from app.db.models import TelemetryEvent
from app.db.models import LocationEvent
from app.db.models import TrackMapPoint 


class TelemetryRepository:
    def get_driver_history(
        self,
        db: Session,
        driver_number: int,
        limit: int = 100,
    ):
        return (
            db.query(TelemetryEvent)
            .filter(TelemetryEvent.driver_number == driver_number)
            .order_by(TelemetryEvent.event_time.desc())
            .limit(limit)
            .all()
        )

    def get_driver_history_by_session(
        self,
        db: Session,
        driver_number: int,
        session_key: int,
        limit: int = 100,
    ):
        return (
            db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.driver_number == driver_number,
                TelemetryEvent.session_key == session_key,
            )
            .order_by(TelemetryEvent.event_time.desc())
            .limit(limit)
            .all()
        )

    def get_available_sessions(self, db: Session):
        return (
            db.query(SessionMetadata)
            .order_by(SessionMetadata.date_start.desc())
            .all()
        )

    def get_drivers_by_session(
        self,
        db: Session,
        session_key: int,
    ):
        return (
            db.query(DriverMetadata)
            .filter(DriverMetadata.session_key == session_key)
            .order_by(DriverMetadata.driver_number)
            .all()
        )

    def count_events(self, db: Session):
        return db.query(TelemetryEvent).count()

    def count_distinct_drivers(self, db: Session):
        return (
            db.query(TelemetryEvent.driver_number)
            .distinct()
            .count()
        )
    
    def get_session_locations(
        self,
        db: Session,
        session_key: int,
        limit: int = 1000,
    ):
        return (
            db.query(LocationEvent)
            .filter(
                LocationEvent.session_key == session_key,
                LocationEvent.x != 0,
                LocationEvent.y != 0,
            )
            .order_by(LocationEvent.event_time.asc())
            .limit(limit)
            .all()
        )
    
    def get_driver_locations_by_session(
        self,
        db: Session,
        session_key: int,
        driver_number: int,
        limit: int = 3000,
    ):
        return (
            db.query(LocationEvent)
            .filter(
                LocationEvent.session_key == session_key,
                LocationEvent.driver_number == driver_number,
                LocationEvent.x != 0,
                LocationEvent.y != 0,
            )
            .order_by(LocationEvent.event_time.asc())
            .limit(limit)
            .all()
        )
    
    def get_track_map(
        self,
        db: Session,
        session_key: int,
    ):
        return (
            db.query(TrackMapPoint)
            .filter(TrackMapPoint.session_key == session_key)
            .order_by(TrackMapPoint.point_order.asc())
            .all()
        )


    def clear_track_map(
        self,
        db: Session,
        session_key: int,
    ):
        (
            db.query(TrackMapPoint)
            .filter(TrackMapPoint.session_key == session_key)
            .delete()
        )


    def save_track_map_points(
        self,
        db: Session,
        points: list[TrackMapPoint],
    ):
        db.add_all(points)

    def get_latest_locations_by_session(
        self,
        db: Session,
        session_key: int,
    ):
        latest_rows = (
            db.query(
                LocationEvent.driver_number,
                func.max(LocationEvent.event_time).label("latest_time"),
            )
            .filter(
                LocationEvent.session_key == session_key,
                LocationEvent.x != 0,
                LocationEvent.y != 0,
            )
            .group_by(LocationEvent.driver_number)
            .subquery()
        )

        return (
            db.query(LocationEvent)
            .join(
                latest_rows,
                (LocationEvent.driver_number == latest_rows.c.driver_number)
                & (LocationEvent.event_time == latest_rows.c.latest_time),
            )
            .filter(LocationEvent.session_key == session_key)
            .order_by(LocationEvent.driver_number)
            .all()
        )
    
    def get_available_years(self, db: Session):
        return (
            db.query(SessionMetadata.year)
            .filter(SessionMetadata.year.isnot(None))
            .distinct()
            .order_by(SessionMetadata.year.desc())
            .all()
        )


    def get_sessions_by_year(
        self,
        db: Session,
        year: int,
    ):
        return (
            db.query(SessionMetadata)
            .filter(SessionMetadata.year == year)
            .order_by(SessionMetadata.date_start.asc())
            .all()
        )