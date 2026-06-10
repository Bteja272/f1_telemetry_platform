import sys
import time

from app.db.database import SessionLocal
from app.db.models import SessionMetadata
from app.scripts.prepare_race import prepare_race


def get_race_sessions_for_year(year: int):
    db = SessionLocal()

    try:
        return (
            db.query(SessionMetadata)
            .filter(
                SessionMetadata.year == year,
                SessionMetadata.session_name == "Race",
            )
            .order_by(SessionMetadata.date_start.asc())
            .all()
        )

    finally:
        db.close()


def prepare_races_for_year(year: int):
    sessions = get_race_sessions_for_year(year)

    if not sessions:
        print(f"No race sessions found for year={year}")
        return

    print(f"Found {len(sessions)} race sessions for {year}")

    successful = 0
    failed = 0

    for session in sessions:
        session_key = session.session_key
        location = session.location
        circuit = session.circuit_short_name

        print("=" * 80)
        print(
            f"Preparing {year} race: "
            f"{location} | {circuit} | session_key={session_key}"
        )

        try:
            prepare_race(session_key=session_key)
            successful += 1

        except Exception as error:
            failed += 1
            print(
                f"Failed to prepare session_key={session_key}: {error}"
            )

        time.sleep(5)

    print("=" * 80)
    print(
        f"Finished preparing races for {year}. "
        f"successful={successful}, failed={failed}"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError(
            "Please provide a year. Example: "
            "python -m app.scripts.prepare_races_for_year 2024"
        )

    prepare_races_for_year(year=int(sys.argv[1]))