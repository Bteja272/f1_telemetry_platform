from sqlalchemy import text

from app.db.database import Base
from app.db.database import engine

import app.db.models


def initialize_database():
    Base.metadata.create_all(bind=engine)

    with engine.connect() as connection:
        connection.execute(
            text(
                """
                CREATE EXTENSION IF NOT EXISTS timescaledb;
                """
            )
        )

        connection.execute(
            text(
                """
                SELECT create_hypertable(
                    'telemetry_events',
                    'event_time',
                    if_not_exists => TRUE
                );
                """
            )
        )

        connection.execute(
            text(
                """
                SELECT create_hypertable(
                    'location_events',
                    'event_time',
                    if_not_exists => TRUE
                );
                """
            )
        )

        connection.commit()

    print("TimescaleDB initialized successfully")


if __name__ == "__main__":
    initialize_database()