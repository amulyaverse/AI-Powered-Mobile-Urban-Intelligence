# Contributing Guide

Welcome to the SIH'26 Urban Intelligence team. This guide describes how to contribute code, documentation, and work to this repository.

---

## Branch Strategy

```
main  ← stable, always deployable
  ↑
  merge via Pull Request
  ↑
feature branch  ← your working branch
```

**Do not push directly to `main`.** All work goes to a feature branch first.

### Suggested Branch Names

| Member | Branch |
|--------|--------|
| Pranav | `pranav/traffic-ai` |
| Abhinandan | `abhinandan/pothole-ai` |
| Arjun | `arjun/backend` |
| Advika | `advika/frontend-gis` |
| Parminder | `parminder/edge-integration` |

For sub-tasks, extend the branch name:
- `pranav/traffic-ai-vehicle-counting`
- `arjun/backend-events-api`

---

## Workflow

```
1. git checkout main
2. git pull origin main          ← always start from latest main
3. git checkout -b pranav/traffic-ai
4. ... do your work ...
5. git add .
6. git commit -m "feat: add vehicle classification"
7. git push origin pranav/traffic-ai
8. Open a Pull Request on GitHub → main
9. Get at least one review
10. Merge
```

---

## Commit Message Format

Use conventional commits:

```
feat: add pothole detection model
fix: correct vehicle counting boundary
docs: update event schema with status field
refactor: split event generator into functions
test: add confidence threshold tests
```

**Bad commits:**
- `update`
- `changes`
- `final`
- `stuff`
- `asdfgh`

---

## Pull Request Rules

1. **One PR per feature or module area** — keep PRs focused
2. **Add a short description** of what you changed and why
3. **Tag the relevant team member** for review
4. **Ensure the frontend still builds** if you touch any shared config
5. **Update docs** if you change an API contract or model output format
6. **No secrets or API keys** — never commit `.env` files

---

## Development Rules

1. **Never commit directly to `main`** — always use a branch
2. **Pull latest main before starting integration** work
3. **Follow the event schema** in `docs/api/event-schema.md` exactly — do not invent your own format
4. **Test your module locally** before opening a PR
5. **Communicate blockers** immediately — don't wait until the deadline
6. **No scope creep** — future features (ANPR, waterlogging, etc.) are not in scope for SIH'26

---

## Issue Tracking

Use GitHub Issues with these labels:
- `ai` — Traffic AI tasks
- `ml` — Road/pothole AI tasks
- `backend` — Backend API tasks
- `frontend` — Frontend/GIS tasks
- `integration` — Edge/pipeline tasks
- `docs` — Documentation tasks
- `bug` — Bug reports
- `blocked` — Blocked tasks

See `docs/project-board.md` for the full task list.

---

## Questions?

Raise it in your team chat or open a GitHub Issue with the `question` label.
