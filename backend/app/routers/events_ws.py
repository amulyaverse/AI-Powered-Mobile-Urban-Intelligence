"""
routers/events_ws.py
---------------------
WebSocket endpoint that dashboard clients subscribe to for receiving
live event notifications.

Endpoint:
    WS  /api/ws/events

When a bus camera stream produces a new accepted detection, camera_ws.py
calls WSBroadcaster.broadcast(payload), which pushes the payload to all
connections registered here.

The client must send a periodic keep-alive ping (any text message) to
prevent the connection from timing out. The server echoes "pong" back.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ws_broadcaster import get_broadcaster

router = APIRouter(tags=["WebSocket"])


@router.websocket("/api/ws/events")
async def events_feed(ws: WebSocket):
    """
    Push-based live event feed for dashboard clients.

    - On connect: subscribe to the WSBroadcaster.
    - On incoming text: reply with "pong" (keep-alive).
    - On disconnect / error: unsubscribe and clean up.

    Payload shape (same as camera_ws.py output):
    {
        "event_id":             "EVT_abc12345",
        "event_type":           "vehicle_count" | "pothole" | "road_defect",
        "confidence":           0.87,
        "severity":             "low" | "medium" | "high" | "critical",
        "bus_id":               "BUS-001",
        "latitude":             28.5639,
        "longitude":            77.2090,
        "timestamp":            "2026-09-05T18:30:00.000Z",
        "frame_index":          42,
        "frame_coverage_ratio": 0.12,
        "boxes":                [...],
        // Traffic events also include:
        "car_count":     12,
        "bike_count":    5,
        "bus_count":     1,
        "truck_count":   2,
        "total_vehicles": 20,
        "density":       "MEDIUM",
        "density_score": 0.5
    }
    """
    broadcaster = get_broadcaster()
    await ws.accept()
    await broadcaster.subscribe(ws)

    print(f"[EventsWS] Dashboard client connected | total={broadcaster.subscriber_count}")

    try:
        while True:
            msg = await ws.receive_text()
            if msg.strip().lower() == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[EventsWS] Client error: {exc}")
    finally:
        await broadcaster.unsubscribe(ws)
        print(f"[EventsWS] Dashboard client disconnected | remaining={broadcaster.subscriber_count}")
