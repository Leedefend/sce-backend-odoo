# Frontend v0.1 Phase Close (0→1 Prototype)

**Date:** 2026-02-01
**Branch:** `feat/frontend-0to1-plan`

## Phase Goal
Prove the minimal Odoo loop on an independent frontend:

`login → app.init → menu → action → list (tree) → record (form)`

This phase focuses on functional chain viability, not UI polish.

## Scope
### Included
- Vue 3 + Vite monorepo scaffold (`frontend/`)
- Intent-based API wiring (`/api/v1/intent`)
- Session + app.init bootstrap
- Menu → Action resolver
- Read-only TreeView (list) shell
- Read-only FormView (record) shell

### Excluded
- Editing, validation, pagination, sorting
- Complex widgets (o2m/m2m, chatter, kanban)
- Full permissions enforcement (front-end policy)
- Production hardening / CI integration

## Implementation Summary
- **Frontend workspace**: `frontend/` with `apps/web` and `packages/*`.
- **Core intents**:
  - `login` (auth)
  - `app.init` (system.init alias)
  - `api.data` (list/read)
  - `load_view` (form contract)
- **Routes**:
  - `/m/:menuId` → resolve menu → `/a/:actionId`
  - `/a/:actionId` → read list data
  - `/r/:model/:id` → read record + form layout

## Evidence
- Commit: `feat(frontend): v0.1 frontend 0→1 prototype (login → init → menu → list/form)`
- Code location: `frontend/`

## Verification Checklist
Run locally:

```bash
pnpm -C frontend install
pnpm -C frontend lint
pnpm -C frontend typecheck
pnpm -C frontend dev
```

Manual flow:
1) Login
2) Home (menu list)
3) Click menu → list view
4) Click row → record view

## Known Gaps / Follow-up (v0.2)
- Field widgets and type-aware rendering
- Search/sort/pagination
- Permissions/capabilities alignment
- UI contract expansion (tree/search/kanban)
- API error handling / retries / UX polish

## Decision
This phase is **closed** as a prototype milestone.
Next work should treat this as a baseline and move into v0.2 engineering hardening.
