import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

from app.db.database import SessionLocal
from app.db.models import TrackMapPoint


load_dotenv()

OPENF1_BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
TARGET_POINTS = 700
LAP_PADDING_SECONDS = 2


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


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_valid_laps(session_key: int) -> list[dict]:
    laps = fetch_json(
        "laps",
        params={"session_key": session_key},
    )

    valid_laps = [
        lap
        for lap in laps
        if lap.get("driver_number") is not None
        and lap.get("lap_duration") is not None
        and lap.get("date_start") is not None
        and lap.get("lap_number") is not None
    ]

    valid_laps = sorted(
        valid_laps,
        key=lambda lap: lap["lap_duration"],
    )

    print(f"Found {len(valid_laps)} valid laps")
    return valid_laps


def get_location_points(
    session_key: int,
    driver_number: int,
) -> list[dict]:
    points = fetch_json(
        "location",
        params={
            "session_key": session_key,
            "driver_number": driver_number,
        },
    )

    valid_points = [
        point
        for point in points
        if point.get("x") not in (None, 0)
        and point.get("y") not in (None, 0)
        and point.get("date") is not None
    ]

    valid_points = sorted(
        valid_points,
        key=lambda point: point["date"],
    )

    print(
        f"driver={driver_number}: "
        f"{len(valid_points)} valid location points"
    )

    return valid_points


def filter_points_for_lap(
    points: list[dict],
    lap_start: datetime,
    lap_end: datetime,
) -> list[dict]:
    lap_points = []

    for point in points:
        point_time = parse_datetime(point["date"])

        if lap_start <= point_time <= lap_end:
            lap_points.append(point)

    return lap_points


def close_track_loop(points: list[dict]) -> list[dict]:
    if len(points) < 2:
        return points

    return points + [points[0]]


def downsample_points(points: list[dict], target_count: int) -> list[dict]:
    if len(points) <= target_count:
        return points

    step = len(points) / target_count

    return [
        points[int(index * step)]
        for index in range(target_count)
    ]


def save_track_map(
    session_key: int,
    source_driver_number: int,
    source_lap_number: int,
    points: list[dict],
):
    db = SessionLocal()

    try:
        (
            db.query(TrackMapPoint)
            .filter(TrackMapPoint.session_key == session_key)
            .delete()
        )

        sampled_points = downsample_points(points, TARGET_POINTS)

        track_points = [
            TrackMapPoint(
                session_key=session_key,
                point_order=index,
                x=point.get("x"),
                y=point.get("y"),
                source=(
                    f"driver_{source_driver_number}_"
                    f"lap_{source_lap_number}"
                ),
                created_at=datetime.now(timezone.utc),
            )
            for index, point in enumerate(sampled_points)
        ]

        db.add_all(track_points)
        db.commit()

        print(
            f"Built track map for session {session_key}: "
            f"driver={source_driver_number}, "
            f"lap={source_lap_number}, "
            f"{len(points)} lap points -> {len(track_points)} map points"
        )

    except Exception as error:
        db.rollback()
        print("Failed to save track map:", error)

    finally:
        db.close()


def build_track_map(session_key: int):
    laps = get_valid_laps(session_key)

    if not laps:
        print(f"No valid laps found for session {session_key}")
        return

    for lap in laps[:30]:
        driver_number = lap["driver_number"]
        lap_number = lap["lap_number"]
        lap_duration = lap["lap_duration"]

        lap_start = parse_datetime(lap["date_start"])
        lap_end = datetime.fromtimestamp(
            lap_start.timestamp() + lap_duration,
            tz=timezone.utc,
        )

        padded_lap_start = lap_start - timedelta(seconds=LAP_PADDING_SECONDS)
        padded_lap_end = lap_end + timedelta(seconds=LAP_PADDING_SECONDS)

        print(
            f"Trying driver={driver_number}, "
            f"lap={lap_number}, "
            f"duration={lap_duration}"
        )

        points = get_location_points(
            session_key=session_key,
            driver_number=driver_number,
        )

        lap_points = filter_points_for_lap(
            points=points,
            lap_start=padded_lap_start,
            lap_end=padded_lap_end,
        )

        print(f"Lap location points: {len(lap_points)}")

        if len(lap_points) >= 250:
            print("FIRST:", lap_points[0]["x"], lap_points[0]["y"])
            print("LAST :", lap_points[-1]["x"], lap_points[-1]["y"])

            closed_lap_points = close_track_loop(lap_points)

            save_track_map(
                session_key=session_key,
                source_driver_number=driver_number,
                source_lap_number=lap_number,
                points=closed_lap_points,
            )
            return

    print("Could not find a lap with enough location points")


if __name__ == "__main__":
    build_track_map(session_key=9662)