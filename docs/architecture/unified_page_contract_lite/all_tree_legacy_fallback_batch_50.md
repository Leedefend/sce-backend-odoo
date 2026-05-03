# Unified Semantic Page Contract Lite - All Tree Legacy Fallback Batch 50

Date: 2026-05-03
Status: implemented guarded fallback

## 1. Boundary

Layer Target: Frontend Contract Consumer / Lite all_tree Fallback Guard

Module:

- `frontend/apps/web/src/app/runtime`
- `frontend/apps/web/src/app/resolvers`
- `scripts/verify`
- `Makefile`
- `docs/architecture/unified_page_contract_lite`

Reason:

`VITE_LITE_CONTRACT_ROLLOUT=all_tree` must not accidentally capture actions
whose menu metadata omits `view_modes`. In the current demo database, action
`642` resolves to `kanban` from legacy `ui.contract`, while its nav meta does
not expose view modes. That case must stay on the legacy path.

## 2. Rule

When `all_tree` is enabled:

- if nav meta declares `tree` or `list`, Lite can be tried directly
- if nav meta declares a non-tree mode, legacy `ui.contract` is used
- if nav meta has no view mode, frontend first performs legacy `ui.contract`
  preflight to read the backend-owned `view_type`
- only confirmed tree/list actions may continue to `load_contract` Lite preview
- confirmed non-tree actions must not dispatch `load_contract`

This keeps semantics backend-owned and prevents frontend guessing.

## 3. Browser Negative

Target:

```bash
make verify.unified_page_contract.lite.all_tree_legacy_browser.host
```

Default action:

```text
LITE_ALL_TREE_LEGACY_ACTION_ID=642
```

The smoke asserts:

- frontend is running with `VITE_LITE_CONTRACT_ROLLOUT=all_tree`
- the non-tree action opens through `/a/<action_id>`
- action-phase `ui.contract` is used
- action-phase `load_contract` is not called
- the page is not blank
- there are no browser console or page errors

## 4. Positive Smoke Adjustment

For tree/list actions whose nav meta does not expose `view_modes`, one
action-phase `ui.contract` preflight is allowed before Lite preview. Repeated
`ui.contract` calls are still blocked by the positive all_tree smoke.

## 5. Explicitly Not Changed

This batch:

- does not make Lite the default
- does not change `login`
- does not change `system.init`
- does not remove legacy fallback
- does not add mobile contract fields
- does not add runtimeContract
- does not change backend contract shape

## 6. Rollback

Runtime rollback:

```text
unset VITE_LITE_CONTRACT_ROLLOUT
```

Code rollback:

```text
revert this batch commit
```
