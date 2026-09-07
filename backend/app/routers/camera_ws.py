"""
routers/camera_ws.py
---------------------
WebSocket endpoint that accepts a JPEG frame stream from a dedicated edge
device / bus camera and runs real-time YOLO inference on sampled frames.

Endpoint:
    WS  /api/ws/camera/{bus_id}?lat=<float>&lng=<float>&mode=traffic|pothole

Message protocol:
    Client → Server : raw binary JPEG bytes (one frame per message)
    Server → Client : JSON   {event_id, event_type, confidence, severity,
                               frame_index, frame_coverage_ratio, boxes, ...}
                      or      {"status": "frame_skipped", "frame_index": N}
                      or      {"status": "no_detection", "frame_index": N}

Frame sampling:
    Inference is run at most every WS_FRAME_SAMPLE_INTERVAL_SEC (0.5 s = 2 fps).
    Frames arriving between sample windows are acknowledged with a "frame_skipped"
    message so the edge device knows the connection is alive.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Literal

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.event import Event
from app.models.bus import Bus
from app.models.ws_session import WsSession
from app.services.inference_engine import InferenceEngine
from app.services.event_aggregator import get_aggregator
from app.services.ws_broadcaster import get_broadcaster
from app.services.hotspot_service import process_event_for_hotspot
from app.services.bus_service import upsert_bus

router = APIRouter(tags=["WebSocket"])
settings = get_settings()


# ── DB dependency (sync, used via thread executor) ────────────────────────────

def _get_db() -> Session:
    return SessionLocal()


def _get_bus_coordinates_sync(bus_id: str, fallback_lat: float | None, fallback_lng: float | None) -> tuple[float, float]:
    """Retrieve the bus's current Delhi coordinates from DB, or fallback."""
    db = _get_db()
    try:
        bus = db.query(Bus).filter(Bus.id == bus_id).first()
        if bus and bus.last_lat is not None and bus.last_lng is not None:
            return bus.last_lat, bus.last_lng
        if fallback_lat is not None and fallback_lng is not None:
            return fallback_lat, fallback_lng
        from app.services.bus_location_service import get_random_delhi_coordinates
        rnd_lat, rnd_lng, _ = get_random_delhi_coordinates()
        return rnd_lat, rnd_lng
    finally:
        db.close()





# ── Synchronous event ingestion (run in a thread executor) ───────────────────

def _ingest_event_sync(
    bus_id: str,
    lat: float,
    lng: float,
    result,  # InferenceResult
    ws_session_id: int | None,
    frame: np.ndarray | None = None,
) -> Event:
    """
    Persist an InferenceResult as an Event row with real captured frame evidence.
    Runs synchronously in a thread pool so it doesn't block the event loop.
    """
    import uuid

    db = _get_db()
    try:
        upsert_bus(db, bus_id, lat, lng, result.density)
        db.flush()

        assigned_id = f"EVT_{uuid.uuid4().hex[:8]}"
        evidence_path = None
        if frame is not None and getattr(frame, "size", 0) > 0:
            try:
                settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
                img_name = f"{assigned_id}.jpg"
                save_path = settings.EVIDENCE_DIR / img_name
                cv2.imwrite(str(save_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                evidence_path = f"/evidence/{img_name}"
            except Exception as img_err:
                print(f"[CameraWS] Failed to save frame for {assigned_id}: {img_err}")

        event = Event(
            event_id=assigned_id,
            event_type=result.event_type,
            confidence=result.confidence,
            severity=result.severity,
            bus_id=bus_id,
            camera_id="CAM_FRONT",
            latitude=lat,
            longitude=lng,
            timestamp=datetime.now(timezone.utc),
            evidence=evidence_path,
            status="new",
            repeated_detections=1,
            source_frame=result.frame_index,
            frame_coverage_ratio=result.frame_coverage_ratio,
            # Traffic-specific
            car_count=result.car_count,
            bike_count=result.bike_count,
            bus_count=result.bus_count,
            truck_count=result.truck_count,
            total_vehicles=result.total_vehicles,
            density=result.density,
            density_score=result.density_score,
            ws_session_id=str(ws_session_id) if ws_session_id else None,
            # PR 37 & 40 road defect fields
            bbox=(
                f"[{result.boxes[0].x1:.1f}, {result.boxes[0].y1:.1f}, {result.boxes[0].x2:.1f}, {result.boxes[0].y2:.1f}]"
                if result.boxes
                else None
            ),
            width_ratio=result.width_ratio,
            area_ratio=result.area_ratio,
            severity_method=result.severity_method,
            surface_condition=result.surface_condition,
        )
        db.add(event)
        db.flush()

        process_event_for_hotspot(db, event)
        db.commit()
        db.refresh(event)
        return event
    except Exception as exc:
        db.rollback()
        print(f"[CameraWS] Error persisting event for bus {bus_id}: {exc}")
        raise
    finally:
        db.close()


def _update_session_sync(session_id: int, **kwargs) -> None:
    """Update a WsSession row (frames_received, events_emitted, disconnected_at, etc.)."""
    db = _get_db()
    try:
        session = db.query(WsSession).filter(WsSession.id == session_id).first()
        if session:
            for k, v in kwargs.items():
                setattr(session, k, v)
            db.commit()
    finally:
        db.close()


def _create_session_sync(bus_id: str, mode: str) -> int:
    """Insert a new WsSession row and return its ID."""
    db = _get_db()
    try:
        s = WsSession(bus_id=bus_id, mode=mode)
        db.add(s)
        db.commit()
        db.refresh(s)
        return s.id
    finally:
        db.close()


# ── WebSocket handler ─────────────────────────────────────────────────────────

@router.websocket("/api/ws/camera/{bus_id}")
async def camera_stream(
    ws: WebSocket,
    bus_id: str,
    lat: float | None = Query(default=None, description="Current GPS latitude of the bus"),
    lng: float | None = Query(default=None, description="Current GPS longitude of the bus"),
    mode: Literal["traffic", "pothole"] = Query(
        default="traffic",
        description="Inference mode: 'traffic' (vehicle count) or 'pothole' (road damage)",
    ),
):
    """
    Accept binary JPEG frames from an edge device, run YOLO inference at 2 fps,
    persist accepted detections, and broadcast results to subscribed dashboard clients.
    """
    import asyncio
    from app.services.bus_location_service import get_vicinity_coordinates

    await ws.accept()

    aggregator = get_aggregator()
    broadcaster = get_broadcaster()
    engine = InferenceEngine(mode=mode)

    # Log session start (sync, one-off)
    loop = asyncio.get_running_loop()
    session_id: int = await loop.run_in_executor(
        None, _create_session_sync, bus_id, mode
    )

    # Resolve bus base coordinates from DB or fallbacks
    base_lat, base_lng = await loop.run_in_executor(
        None, _get_bus_coordinates_sync, bus_id, lat, lng
    )

    frames_received = 0
    frames_inferred = 0
    events_emitted = 0
    last_inference_at = 0.0

    print(f"[CameraWS] Bus {bus_id} connected at ({base_lat}, {base_lng}) | mode={mode} | session={session_id}")

    try:
        async for raw_bytes in ws.iter_bytes():
            frames_received += 1

            # ── Frame size guard ─────────────────────────────────────────────
            if len(raw_bytes) > settings.WS_MAX_FRAME_SIZE_BYTES:
                await ws.send_json({
                    "status": "frame_rejected",
                    "reason": "frame_too_large",
                    "frame_index": frames_received,
                    "max_bytes": settings.WS_MAX_FRAME_SIZE_BYTES,
                })
                continue

            # ── Frame sampler: skip if too soon ──────────────────────────────
            now = time.monotonic()
            if now - last_inference_at < settings.WS_FRAME_SAMPLE_INTERVAL_SEC:
                await ws.send_json({
                    "status": "frame_skipped",
                    "frame_index": frames_received,
                })
                continue

            last_inference_at = now
            frames_inferred += 1

            # ── Decode JPEG → BGR ndarray ────────────────────────────────────
            arr = np.frombuffer(raw_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                await ws.send_json({
                    "status": "frame_rejected",
                    "reason": "invalid_jpeg",
                    "frame_index": frames_received,
                })
                continue

            # ── YOLO inference (blocking; run in thread pool) ─────────────────
            result = await loop.run_in_executor(
                None, engine.run, frame, frames_received
            )

            if result is None:
                await ws.send_json({
                    "status": "no_detection",
                    "frame_index": frames_received,
                })
                continue

            # ── Temporal deduplication ────────────────────────────────────────
            if not aggregator.should_emit(bus_id, result.event_type, result.confidence):
                # When DB persistence is deduplicated, still send live bounding boxes back
                # to the camera streamer so real-time detection boxes and counts don't flicker off.
                live_payload = result.to_ws_payload(event_id="", evidence=None)
                live_payload["status"] = "streaming"
                live_payload["bus_id"] = bus_id
                live_payload["latitude"] = base_lat
                live_payload["longitude"] = base_lng
                await ws.send_json(live_payload)
                continue

            # Compute detection coordinates strictly within 3 km vicinity of bus
            det_lat, det_lng = get_vicinity_coordinates(
                base_lat, base_lng, max_radius_km=settings.BUS_VICINITY_RADIUS_KM, step=events_emitted + 1
            )

            # ── Persist event (blocking DB write in thread pool) ──────────────
            event = await loop.run_in_executor(
                None,
                _ingest_event_sync,
                bus_id, det_lat, det_lng, result, session_id, frame,
            )

            aggregator.record(bus_id, result.event_type, result.confidence)
            events_emitted += 1

            # ── Respond to publisher & broadcast ──────────────────────────────
            payload = result.to_ws_payload(event_id=event.event_id, evidence=event.evidence)
            payload["bus_id"] = bus_id
            payload["camera_id"] = "CAM_FRONT"
            payload["status"] = event.status or "new"
            payload["repeated_detections"] = event.repeated_detections or 1
            payload["latitude"] = det_lat
            payload["longitude"] = det_lng
            event_ts = event.timestamp
            if event_ts.tzinfo is None:
                event_ts = event_ts.replace(tzinfo=timezone.utc)
            payload["timestamp"] = event_ts.isoformat()
            payload["evidence"] = event.evidence

            await ws.send_json(payload)

            # ── Broadcast to all dashboard clients ────────────────────────────
            await broadcaster.broadcast(payload)

    except WebSocketDisconnect:
        print(f"[CameraWS] Bus {bus_id} disconnected | frames={frames_received} | events={events_emitted}")
    except asyncio.CancelledError:
        print(f"[CameraWS] Bus {bus_id} session cancelled | frames={frames_received} | events={events_emitted}")
    except Exception as exc:
        print(f"[CameraWS] Unexpected error for bus {bus_id}: {exc}")
    finally:
        # Flush session stats directly to DB
        try:
            _update_session_sync(
                session_id,
                disconnected_at=datetime.now(timezone.utc),
                frames_received=frames_received,
                frames_inferred=frames_inferred,
                events_emitted=events_emitted,
            )
        except Exception as err:
            print(f"[CameraWS] Session flush error: {err}")
        aggregator.reset(bus_id)
