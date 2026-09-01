# Project Task Board

> GitHub Projects board: **SIH'26 Urban Intelligence Development**
>
> If you have access to GitHub Projects, create a board with these columns:
> `Backlog` · `To Do` · `In Progress` · `Review` · `Done` · `Blocked`
>
> Use the tasks below as initial issues. Assign labels and owners accordingly.

---

## Traffic AI  — Owner: Pranav

| Task | Label | Priority |
|------|-------|----------|
| `[AI]` Vehicle detection and classification prototype | `ai`, `traffic` | High |
| `[AI]` Vehicle counting logic | `ai`, `traffic` | High |
| `[AI]` Traffic density estimation | `ai`, `traffic` | Medium |

---

## Road AI  — Owner: Abhinandan

| Task | Label | Priority |
|------|-------|----------|
| `[ML]` Select pothole dataset / model | `ml`, `road` | High |
| `[ML]` Pothole detection prototype | `ml`, `road` | High |
| `[ML]` Confidence and severity scoring logic | `ml`, `road` | Medium |

---

## Backend  — Owner: Arjun

| Task | Label | Priority |
|------|-------|----------|
| `[BE]` Design event database schema | `backend` | High |
| `[BE]` Implement POST /api/events | `backend` | High |
| `[BE]` Implement GET /api/events | `backend` | High |
| `[BE]` Implement analytics endpoints | `backend` | Medium |
| `[BE]` Implement GET /api/hotspots | `backend` | Medium |

---

## Frontend / GIS  — Owner: Advika

| Task | Label | Priority |
|------|-------|----------|
| `[FE]` Finalize dashboard from existing prototype | `frontend` | High |
| `[FE]` Connect GIS map to real event data | `frontend` | High |
| `[FE]` Add event detail view (real data) | `frontend` | Medium |
| `[FE]` Add analytics charts and heatmap (real data) | `frontend` | Medium |

---

## Edge / Integration  — Owner: Parminder

| Task | Label | Priority |
|------|-------|----------|
| `[EDGE]` Video input pipeline | `integration` | High |
| `[EDGE]` Event generator (AI → schema) | `integration` | High |
| `[EDGE]` GPS simulation from CSV | `integration` | Medium |
| `[EDGE]` AI-to-backend HTTP integration | `integration` | High |

---

## System Integration  — Owner: Team Lead

| Task | Label | Priority |
|------|-------|----------|
| `[INT]` First end-to-end pipeline (Video → Dashboard) | `integration` | Critical |
| `[INT]` Persistent defect detection logic | `integration` | High |
| `[INT]` Maintenance priority scoring | `integration` | Medium |
| `[INT]` Full system test | `integration` | High |

---

## Submission  — Owner: Team Lead

| Task | Label | Priority |
|------|-------|----------|
| `[DOC]` Final README | `docs` | High |
| `[DOC]` 6-page PPT | `docs` | High |
| `[DOC]` Demo video with voiceover | `docs` | High |
| `[DOC]` Full stack deployment | `deployment` | High |
| `[DOC]` Final repository audit | `docs` | High |

---

## How to Use This with GitHub Issues

1. Go to your repo → **Issues** → **New Issue**
2. Use the Task template (`.github/ISSUE_TEMPLATE/task.md`)
3. Title: copy the task name from above (e.g. `[AI] Vehicle detection and classification prototype`)
4. Assign to the relevant team member
5. Add labels: `ai`, `ml`, `backend`, `frontend`, `integration`, `docs`
6. Go to **Projects** → Add to the project board in the right column

Recommended labels to create on GitHub:
`ai` · `ml` · `backend` · `frontend` · `integration` · `docs` · `deployment` · `bug` · `blocked`
