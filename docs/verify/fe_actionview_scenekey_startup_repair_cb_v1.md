# FE ActionView SceneKey Startup Repair CB

## Goal

Align the scene identity sources used by the frontend startup chain so
scene-first routes keep their scene key when ActionView bootstraps.

## Scope

- router static scene entry metadata
- ActionView scene key resolution
- no backend changes

## Implemented Change

1. `/s/project.management` already carries stable `meta.sceneKey` through the
   router-side startup alignment patch.
2. `ActionView` now treats any real scene-first route context as
   `keepSceneRoute=true`, not only the generic `scene` route name.
3. This keeps follow-up action navigation on the current `/s/...` path instead
   of degrading toward removed non-scene action routes.

## Verification Plan

1. Validate the active task contract.
2. Re-run frontend typecheck and build.
3. Restart frontend and execute the real browser smoke for
   `/s/project.management`.

## Checkpoint Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-ACTIONVIEW-SCENEKEY-STARTUP-REPAIR-CB.yaml`: PASS
- `pnpm -C frontend/apps/web build`: PASS
  - existing chunk-size warning only
- `git diff --check -- ...`: PASS
- live browser smoke:
  - `make frontend.restart`: PASS
  - `make verify.portal.project_dashboard_primary_entry_browser_smoke.host ...`: no clean PASS/FAIL verdict in this batch; browser run stalled in-page and did not finish in bounded time
  - latest prior failure evidence under `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T051322Z/summary.json` still shows repeated `ERR_NETWORK_CHANGED`, consistent with a residual request-loop or route-churn symptom

## Current Decision

Static startup-alignment patch is in place and low-risk, but live verification is
still conditional. The next bounded step should stay on the frontend consumer
side and isolate the remaining in-page request churn inside the generic
`/s/project.management` consumption path.
