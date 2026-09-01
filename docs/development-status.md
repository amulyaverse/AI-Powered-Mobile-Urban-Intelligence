# Development Status

> Last updated: 1 September 2026. Update this file as module status changes.

| Module | Owner | Status | Next Deliverable |
|--------|-------|--------|-----------------|
| Traffic AI | Pranav | 🟡 In Progress | Vehicle detection + counting on test video |
| Road AI | Abhinandan | 🟡 In Progress | Pothole model running on sample images |
| Backend | Arjun | 🔵 Planned | Events API (POST + GET /api/events) |
| Frontend / GIS | Advika | ✅ Prototype | Prepare API integration (replace mock data) |
| Edge / Integration | Parminder | 🔵 Planned | Video → AI → event pipeline (console output) |
| System Integration | Team Lead | 🟡 In Progress | Architecture, docs, end-to-end integration |

---

## Status Key

| Icon | Meaning |
|------|---------|
| ✅ | Complete / working |
| 🟡 | In progress |
| 🔵 | Planned — not started |
| 🔴 | Blocked |

---

## Frontend

The React/Vite frontend prototype is **complete and deployed**.

- Live URL: https://ai-powered-mobile-urban-intelligenc.vercel.app/
- Running on: **mock data only**
- All pages built: Overview, Live Monitoring, Events, GIS Map, Traffic Analytics, Road Analytics
- Service layer ready for backend connection: `frontend/src/services/api.js`

**Next step for Advika:** When the backend API is ready, update `src/services/api.js` to call the real backend. See `docs/api/event-schema.md` for the expected API format.

---

## Traffic AI

**Next steps for Pranav:**
1. Choose and download a traffic dataset (COCO, VisDrone, or similar)
2. Train or fine-tune YOLOv8 for vehicle detection and classification
3. Implement vehicle counting logic (line crossing or zone-based)
4. Compute a traffic density estimate from the count
5. Output a Python dict matching the event schema

---

## Road AI

**Next steps for Abhinandan:**
1. Choose a pothole/road damage dataset (RDD2022, Pothole-600, or similar)
2. Train or fine-tune a detection model
3. Compute a severity estimate from bounding box size and confidence
4. Output a Python dict matching the event schema

---

## Backend

**Next steps for Arjun:**
1. Set up FastAPI (or Flask) project in `backend/api/`
2. Design the event database schema (based on `docs/api/event-schema.md`)
3. Implement `POST /api/events` to store incoming events
4. Implement `GET /api/events` to return events with optional filters
5. Add CORS headers so the frontend can connect
6. Test with a sample curl request

---

## Integration / Edge

**Next steps for Parminder:**
1. Set up a Python script that reads video frame-by-frame
2. Call Pranav's traffic AI function + Abhinandan's road AI function per frame
3. Format the output as an event (attach GPS, timestamp, event_id)
4. POST the event to the backend
5. Start with hardcoded GPS coordinates, add CSV-based GPS simulation later
