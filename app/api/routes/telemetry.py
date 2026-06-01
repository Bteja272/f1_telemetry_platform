from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.services.telemetry_service import TelemetryService

router = APIRouter(tags=["Telemetry"])
telemetry_service = TelemetryService()


@router.get("/sessions")
def get_available_sessions(db: Session = Depends(get_db)):
    sessions = telemetry_service.get_available_sessions(db)

    return {
        "count": len(sessions),
        "sessions": sessions,
    }


@router.get("/sessions/{session_key}/drivers")
def get_drivers_by_session(
    session_key: int,
    db: Session = Depends(get_db),
):
    drivers = telemetry_service.get_drivers_by_session(
        db=db,
        session_key=session_key,
    )

    return {
        "session_key": session_key,
        "count": len(drivers),
        "drivers": drivers,
    }


@router.get("/drivers/{driver_number}/latest")
def get_latest_driver_state(driver_number: int):
    latest_state = telemetry_service.get_latest_driver_state(driver_number)

    if not latest_state:
        raise HTTPException(
            status_code=404,
            detail="No latest telemetry found for this driver",
        )

    return latest_state


@router.get("/drivers/{driver_number}/history")
def get_driver_history(
    driver_number: int,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    history = telemetry_service.get_driver_history(
        db=db,
        driver_number=driver_number,
        limit=limit,
    )

    return {
        "driver_number": driver_number,
        "count": len(history),
        "telemetry": history,
    }


@router.get("/sessions/{session_key}/drivers/{driver_number}/history")
def get_driver_history_by_session(
    session_key: int,
    driver_number: int,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    history = telemetry_service.get_driver_history_by_session(
        db=db,
        driver_number=driver_number,
        session_key=session_key,
        limit=limit,
    )

    return {
        "session_key": session_key,
        "driver_number": driver_number,
        "count": len(history),
        "telemetry": history,
    }


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    return telemetry_service.get_metrics(db)

@router.get("/sessions/{session_key}/locations")
def get_session_locations(
    session_key: int,
    limit: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    locations = telemetry_service.get_session_locations(
        db=db,
        session_key=session_key,
        limit=limit,
    )

    return {
        "session_key": session_key,
        "count": len(locations),
        "locations": locations,
    }