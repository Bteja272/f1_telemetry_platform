import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert

from app.db.database import SessionLocal
from app.db.models import SessionMetadata


load_dotenv()

OPENF1_BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")


def parse_datetime(value: str | None):
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_json(endpoint: str, params: dict | None = None) -> list[dict]:
    url = f"{OPENF1_BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        params=params or {},
        timeout=30,
    )

    print(f"{endpoint} URL:", response.url)
    print(f"{endpoint} status:", response.status_code)

    response.raise_for_status()
    return response.json()


def save_session(session: dict):
    db = SessionLocal()

    try:
        date_start = parse_datetime(session.get("date_start"))

        statement = insert(SessionMetadata).values(
            session_key=session.get("session_key"),
            meeting_key=session.get("meeting_key"),
            session_name=session.get("session_name"),
            session_type=session.get("session_type"),
            date_start=date_start,
            date_end=parse_datetime(session.get("date_end")),
            location=session.get("location"),
            country_name=session.get("country_name"),
            circuit_short_name=session.get("circuit_short_name"),
            year=date_start.year if date_start else None,
        )

        statement = statement.on_conflict_do_update(
            index_elements=["session_key"],
            set_={
                "meeting_key": statement.excluded.meeting_key,
                "session_name": statement.excluded.session_name,
                "session_type": statement.excluded.session_type,
                "date_start": statement.excluded.date_start,
                "date_end": statement.excluded.date_end,
                "location": statement.excluded.location,
                "country_name": statement.excluded.country_name,
                "circuit_short_name": statement.excluded.circuit_short_name,
                "year": statement.excluded.year,
            },
        )

        db.execute(statement)
        db.commit()

        print(
            f"Saved session: "
            f"{session.get('location')} | "
            f"{session.get('circuit_short_name')} | "
            f"{session.get('date_start')}"
        )

    except Exception as error:
        db.rollback()
        print("Failed to save session:", error)

    finally:
        db.close()


def load_race_sessions_for_year(year: int):
    sessions = fetch_json(
        "sessions",
        params={
            "year": year,
            "session_name": "Race",
        },
    )

    print(f"Found {len(sessions)} race sessions for {year}")

    for session in sessions:
        save_session(session)


if __name__ == "__main__":
    for year in [2023, 2024, 2025, 2026]:
        load_race_sessions_for_year(year)