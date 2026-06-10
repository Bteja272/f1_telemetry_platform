import sys

from app.producer.openf1_producer import get_drivers_for_session
from app.scripts.build_track_map import build_track_map


def prepare_race(session_key: int):
    print(f"Preparing race session_key={session_key}")

    print("Loading driver metadata...")
    drivers = get_drivers_for_session(session_key)

    print(f"Loaded {len(drivers)} drivers")

    print("Building track map...")
    build_track_map(session_key=session_key)

    print(f"Race preparation complete for session_key={session_key}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError(
            "Please provide a session_key. Example: "
            "python -m app.scripts.prepare_race 9662"
        )

    prepare_race(session_key=int(sys.argv[1]))