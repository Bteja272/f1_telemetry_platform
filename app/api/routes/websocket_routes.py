import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.cache.redis_client import redis_client
from app.websocket.connection_manager import manager

router = APIRouter(tags=["WebSocket"])


def parse_redis_driver_state(driver_number: int, data: dict):
    return {
        "driver_number": driver_number,
        "speed": float(data.get("speed", 0)),
        "rpm": int(data.get("rpm", 0)),
        "gear": int(data.get("gear", 0)),
        "throttle": float(data.get("throttle", 0)),
        "brake": float(data.get("brake", 0)),
        "drs": int(data.get("drs", 0)),
        "event_time": data.get("event_time"),
        "session_key": int(data.get("session_key", 0)),
        "meeting_key": int(data.get("meeting_key", 0)),
    }


@router.websocket("/ws/telemetry/{driver_number}")
async def stream_driver_telemetry(websocket: WebSocket, driver_number: int):
    await manager.connect(websocket)

    try:
        while True:
            redis_key = f"driver:{driver_number}:latest"
            data = redis_client.hgetall(redis_key)

            if data:
                await manager.send_json(
                    websocket,
                    parse_redis_driver_state(driver_number, data),
                )
            else:
                await manager.send_json(
                    websocket,
                    {
                        "driver_number": driver_number,
                        "message": "No telemetry found yet",
                    },
                )

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/telemetry")
async def stream_all_latest_telemetry(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            keys = redis_client.keys("driver:*:latest")
            payload = []

            for key in keys:
                data = redis_client.hgetall(key)

                try:
                    driver_number = int(key.split(":")[1])
                except Exception:
                    continue

                if data:
                    payload.append(parse_redis_driver_state(driver_number, data))

            await manager.send_json(
                websocket,
                {
                    "type": "telemetry_batch",
                    "count": len(payload),
                    "drivers": payload,
                },
            )

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)