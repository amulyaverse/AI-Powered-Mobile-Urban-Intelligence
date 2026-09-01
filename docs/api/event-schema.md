# Event Schema — Integration Contract

> **This is the single shared contract between all modules.**
> Every team member must produce or consume events in exactly this format.
> Do not change this schema without team discussion.

---

## The Event Object

```json
{
  "event_id": "EVT_001",
  "event_type": "pothole",
  "confidence": 0.92,
  "severity": "high",
  "bus_id": "BUS_021",
  "camera_id": "CAM_FRONT",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "timestamp": "2026-09-01T10:42:17Z",
  "evidence": "/evidence/EVT_001.jpg",
  "status": "new"
}
```

---

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | `string` | ✅ | Unique identifier. Format: `EVT_<number>` or UUID. |
| `event_type` | `string` | ✅ | Type of detection. See allowed values below. |
| `confidence` | `float` | ✅ | AI model confidence score. Range: `0.0` – `1.0`. |
| `severity` | `string` | ✅ | Categorical severity. See allowed values below. |
| `bus_id` | `string` | ✅ | Unique identifier of the reporting bus. Format: `BUS_<number>`. |
| `camera_id` | `string` | ✅ | Identifier of the camera on the bus. E.g. `CAM_FRONT`, `CAM_REAR`. |
| `latitude` | `float` | ✅ | GPS latitude at time of detection. Decimal degrees. |
| `longitude` | `float` | ✅ | GPS longitude at time of detection. Decimal degrees. |
| `timestamp` | `string` | ✅ | ISO 8601 UTC timestamp. Format: `YYYY-MM-DDTHH:MM:SSZ`. |
| `evidence` | `string` | ✅ | File path, URL, or base64 image of the detection evidence. |
| `status` | `string` | ✅ | Processing status. Set by backend. AI modules should send `"new"`. |

---

## Allowed Values

### `event_type`

| Value | Description |
|-------|-------------|
| `pothole` | A pothole detected in the road surface |
| `road_defect` | General road damage (crack, erosion, etc.) |
| `congestion` | High vehicle density / traffic jam |
| `vehicle_count` | Periodic vehicle count observation |

### `severity`

| Value | Meaning |
|-------|---------|
| `low` | Minor issue, monitor |
| `medium` | Notable issue, schedule inspection |
| `high` | Significant issue, prioritize repair |
| `critical` | Immediate action required |

### `status`

| Value | Set By |
|-------|--------|
| `new` | Edge AI / Integration module |
| `under_review` | Authority / backend logic |
| `verified` | Authority confirms the issue |
| `resolved` | Repair or resolution confirmed |

---

## Module Contracts

### AI Module Output (Pranav / Abhinandan)

The AI module must produce a Python dict with these fields for every detection above the confidence threshold:

```python
{
    "event_type": "pothole",       # string
    "confidence": 0.87,            # float 0-1
    "severity": "medium",          # computed from confidence + size
    "bus_id": "BUS_021",           # passed in from environment/config
    "camera_id": "CAM_FRONT",      # passed in from config
    "latitude": 28.6139,           # from GPS module
    "longitude": 77.2090,          # from GPS module
    "timestamp": "2026-09-01T10:42:17Z",  # current UTC time
    "evidence": "/tmp/frame_001.jpg"       # saved frame path
}
```

The `event_id` and `status` fields are assigned by the Integration layer / Backend.

---

### Integration Layer Output (Parminder)

The integration layer wraps the AI output with a generated `event_id`, sets `status` to `"new"`, and sends it to the backend:

```python
event = {
    "event_id": str(uuid.uuid4()),
    "status": "new",
    **ai_output  # merge with AI module dict above
}
requests.post("http://backend/api/events", json=event)
```

---

### Backend Input (Arjun)

The backend `POST /api/events` endpoint accepts the complete event object above and stores it.

**Minimum backend endpoints required:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/events` | Ingest a new event from the integration layer |
| `GET` | `/api/events` | Return all events (with optional filters) |
| `GET` | `/api/events/{event_id}` | Return a single event by ID |
| `GET` | `/api/analytics/summary` | Return aggregated counts for the dashboard |
| `GET` | `/api/hotspots` | Return persistent detection hotspots |

---

### Frontend Input (Advika)

The frontend fetches events from `GET /api/events` and replaces the mock data in `src/services/api.js`.

The frontend already consumes this exact schema — see `src/data/mockData.js` for reference.

To connect: replace the `return mockData` lines in `src/services/api.js` with actual `fetch()` calls to the backend URL.

---

## Minimum Confidence Threshold

Events should only be generated when `confidence >= 0.65`.

Events with confidence below this threshold should be discarded by the integration layer.

---

## GPS Coordinate Precision

Use at least **4 decimal places** for latitude and longitude.  
Example: `28.6139` (not `28.61`).

For persistent detection matching, the backend will cluster events within a **50-metre radius** of each other.

