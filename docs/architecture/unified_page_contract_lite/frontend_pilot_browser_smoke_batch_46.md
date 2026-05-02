# Unified Semantic Page Contract Lite - Frontend Pilot Browser Smoke Batch 46

Date: 2026-05-02
Status: acceptance smoke added

## 1. Boundary

Layer Target: Frontend Verification / Lite Pilot Browser Smoke

Module:

- `scripts/verify`
- `Makefile`
- `docs/architecture/unified_page_contract_lite`

Reason:

The frontend pilot implementation must be accepted by a real browser path, not
only by static type and source guards.

## 2. Acceptance Scope

Pilot page:

```text
project.project:tree
```

Required dev server flag:

```text
VITE_LITE_CONTRACT_PILOT=1
```

Acceptance target:

```bash
make verify.unified_page_contract.lite.frontend_pilot_browser.host
```

## 3. Browser Assertions

The smoke verifies:

- login succeeds against the selected development database
- the pilot action route opens the project tree page
- action-phase contract loading dispatches `load_contract`
- `load_contract` returns `load_contract Lite preview`
- the action phase has no `ui.contract` fallback
- rendered project list contains at least one table row
- browser console and page errors are absent

## 4. Explicitly Not Changed

This batch does not:

- enable Lite pilot by default
- expand beyond `project.project:tree`
- replace the global frontend renderer
- require browser smoke inside the default quick gate

## 5. Rollback

Runtime rollback:

```text
start the frontend without VITE_LITE_CONTRACT_PILOT=1
```

Code rollback:

```text
revert this batch commit
```
