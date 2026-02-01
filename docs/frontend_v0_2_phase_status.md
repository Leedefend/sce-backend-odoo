# Frontend v0.2 Phase Status (Session + Contract Stabilization)

**Date:** 2026-02-01
**Branch:** `feat/frontend-v0_2-session-contract`

## Phase Goal
Stabilize the 0→1 loop to survive refreshes, concurrent requests, and contract drift:

`login → app.init → menu → action → list/form`

## Scope
### Included
- Session persistence + readiness guards
- Cross-origin credentials (cookie/session) handling
- Trace ID propagation and request logging
- Contract typing and field selection from view contracts
- Action context/domain merge + menu routing params

### Excluded
- Edit/write flows
- Pagination/sort/search UX
- Widget richness (o2m/m2m/chatter)
- Permission reasoning on frontend (still backend-driven)

## Implemented Work
### P0 (401/CORS/Session transport)
- `fetch` uses `credentials: "include"`
- `X-Trace-Id` consistently attached
- Backend CORS allows `X-Trace-Id`, `X-Tenant`

### P1 (Session productization)
- Session restore from localStorage + token from sessionStorage
- `logout()` clears token + cache
- `isReady` guard ensures app.init before route entry

### P2 (Contract typing + field selection)
- Added Intent/ApiData/LoadView types
- Action list uses `ui.contract` to determine columns
- Form view uses layout-defined fields (fallback only if empty)

### P3 (Action semantics)
- `/m/:menuId` redirects to `/a/:actionId?menu_id=...`
- Action context merged with `menu_id`
- Domain passed through to api.data list

## Commits (per phase)
1) `feat(session): allow intent headers + trace + credentials`
2) `feat(session): restore/logout/isReady guard`
3) `feat(contract): schema types + action contract fields`
4) `feat(action): menu context merge + route params`

## Verification Checklist
```bash
pnpm -C frontend install
pnpm -C frontend lint
pnpm -C frontend typecheck
pnpm -C frontend dev
```

Manual flow:
1) Login
2) Refresh page (session persists)
3) Menu → list → record
4) No 401 in Network panel; trace IDs visible in logs

## Known Gaps / Next Phase (v0.3)
- Tree/Form field widgets + type-aware rendering
- Search, sort, pagination alignment with Odoo
- Permission/capability overlays
- UI contract expansion (tree/search/kanban)

## Decision
Phase v0.2 is **ready for review** pending local verification.
