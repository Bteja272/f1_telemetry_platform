from sqlalchemy.orm import Session

from app.db.models import TelemetryEvent


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

    def count_events(self, db: Session):
        return db.query(TelemetryEvent).count()

    def count_distinct_drivers(self, db: Session):
        return (
            db.query(TelemetryEvent.driver_number)
            .distinct()
            .count()
        )