from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String

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


class SessionMetadata(Base):
    __tablename__ = "session_metadata"

    session_key = Column(Integer, primary_key=True, nullable=False)
    meeting_key = Column(Integer)

    session_name = Column(String)
    session_type = Column(String)

    date_start = Column(DateTime(timezone=True))
    date_end = Column(DateTime(timezone=True))

    location = Column(String)
    country_name = Column(String)
    circuit_short_name = Column(String)
    year = Column(Integer)


class DriverMetadata(Base):
    __tablename__ = "driver_metadata"

    driver_number = Column(Integer, primary_key=True, nullable=False)
    session_key = Column(Integer, primary_key=True, nullable=False)

    full_name = Column(String)
    broadcast_name = Column(String)
    name_acronym = Column(String)

    team_name = Column(String)
    team_colour = Column(String)

    first_name = Column(String)
    last_name = Column(String)
    country_code = Column(String)
    headshot_url = Column(String)