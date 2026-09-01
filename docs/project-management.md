# Project Management

> This document governs how the SIH'26 Urban Intelligence team works and what we are building.

---

## Team Roles & Ownership

> These are **initial suggested ownership areas**, not rigid assignments. Members may collaborate, divide work further, or exchange responsibilities. What matters is that every deliverable has a named owner.

| Member | Primary Area | Key Deliverable |
|--------|-------------|----------------|
| **Pranav** | Traffic AI / Computer Vision | Vehicle detection, counting, density model |
| **Abhinandan** | ML / Road-Damage AI | Pothole detection, severity scoring model |
| **Arjun** | Backend / Database | REST API, event schema, database |
| **Advika** | Frontend / GIS | Dashboard API integration, heatmaps |
| **Parminder** | Edge AI / Integration | Video pipeline, event generator, GPS sim |
| **Team Lead** | System Integration / Architecture / Coordination / Documentation / Submission | End-to-end integration, README, PPT, demo |

---

## Development Principles

1. **Work as one integrated team.** Modules must connect. An isolated perfect module that cannot be integrated is not a deliverable.
2. **Every module must have a clear input/output contract.** Follow the event schema in `docs/api/event-schema.md` exactly.
3. **Prioritize integration over isolated perfection.** A working 70% that connects to the rest is better than a perfect 100% that is isolated.
4. **Use Git branches.** Never commit experimental work directly to `main`. See `CONTRIBUTING.md`.
5. **Keep documentation updated.** If you change an API contract or model output format, update the docs immediately.
6. **Do not introduce major scope changes without team discussion.** New features not in the MVP need team consensus before development begins.
7. **Communicate blockers early.** If you are blocked, raise it immediately — don't wait until the milestone.

---

## Milestones

### 2 September — Standalone Prototypes
**Goal:** Each module has a working standalone prototype.

| Module | Deliverable |
|--------|------------|
| Traffic AI | Vehicle detection + classification running on test video |
| Road AI | Pothole detection running on sample images |
| Backend | Basic FastAPI/Flask server with POST /events endpoint |
| Frontend | Dashboard reviewed against backend API contract |
| Integration | Video → AI → basic event dict printed to console |

---

### 3–4 September — First End-to-End Pipeline
**Goal:** One complete flow works, even if rough.

```
Video → AI → Event → GPS → Backend → Database → Dashboard
```

- Traffic or pothole detection feeds an event to the backend
- Backend stores it in the database
- Dashboard fetches and displays it on the GIS map
- GPS coordinates are simulated (hardcoded or from a CSV)

---

### 5 September — Reliability + Analytics + Heatmaps
**Goal:** The pipeline works consistently with real data.

- Multiple event types flowing end-to-end
- Analytics endpoints working (counts by type, severity)
- Dashboard heatmap rendering real events
- Both AI modules producing confident detections

---

### 6 September — Persistent Detection + Priority Scoring
**Goal:** The intelligence layer is working.

- Backend detects when multiple buses have flagged the same GPS location
- Persistent defects generate higher-severity alerts
- Maintenance priority score calculated per hotspot
- Dashboard shows repeated detection count

---

### 7 September — Deployment + Screenshots + Results
**Goal:** Full system running in a deployed environment.

- Full stack deployed (backend + frontend)
- Evidence screenshots collected
- Demo video recording begun
- Performance numbers noted (detection speed, accuracy)

---

### 8 September — Documentation + PPT + Demo Video
**Goal:** All submission materials ready.

- Root README finalized
- 6-page PPT completed
- Demo video with voiceover recorded
- All docs updated to reflect final state

---

### 9 September — Full Testing + Repository Audit + Rehearsal
**Goal:** Repository is clean and submission-ready.

- All modules tested end-to-end
- No broken files, placeholder text, or debug code in main
- Repository structure reviewed
- Demo rehearsed

---

### 10 September — Final Submission
**Goal:** Submit.

- Repository link submitted
- PPT submitted
- Demo video submitted
- Live deployment link submitted

