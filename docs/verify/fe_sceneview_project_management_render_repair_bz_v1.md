# FE SceneView Project Management Render Repair BZ

## Goal

Keep the generic `SceneView` consumer on a stable `/s/project.management`
scene-first path after retiring the dedicated route binding.

## Implemented Change

1. `SceneView` no longer strips query state just because `target.route` matches
   the same scene path with additional embedded action query.
2. Workspace scene pre-redirect now checks path identity only, so
   `/s/project.management?action_id=...` is treated as a self-routed scene
   instead of being normalized back to a bare path on every pass.
3. `SceneView` re-resolve is now keyed to scene identity and render-target
   fields, not the entire `route.fullPath`, so embedded ActionView route-state
   sync does not continuously retrigger scene bootstrap.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-SCENEVIEW-PROJECT-MANAGEMENT-RENDER-REPAIR-BZ.yaml`: PASS
- `pnpm -C frontend/apps/web typecheck:strict`: PASS
- `pnpm -C frontend/apps/web build`: PASS
  - existing chunk-size warning only
- `make frontend.restart`: PASS
- `git diff --check -- ...`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host ...`: FAIL
  - artifact: `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T053757Z/summary.json`
  - failure changed from prior in-page churn to launch/navigation failure:
    `semantic entry navigation failed after recovery attempts (6 tries)`
  - detailed recovery log shows repeated `page.goto ... ERR_CONNECTION_REFUSED`
    against `http://127.0.0.1:5174/?db=sc_demo` and `http://localhost:5174/?db=sc_demo`

## Decision

This batch improved the generic scene consumer guardrails and removed the
strongest self-induced route churn inside `SceneView`, but the acceptance gate
still fails in live verification. The current blocker is no longer a cleanly
proven `SceneView` logic loop; it is a verify-stage runtime/entry failure, so
the batch must stop on `verify_failed`.
