from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer

from app.db.database import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    event_time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    driver_number = Column(Integer, primary_key=True, nullable=False)

    ingested_at = Column(DateTime(timezone=True), nullable=False)

    meeting_key = Column(Integer)
    session_key = Column(Integer)

    speed = Column(Float)
    rpm = Column(Integer)
    gear = Column(Integer)

    throttle = Column(Float)
    brake = Column(Float)
    drs = Column(Integer)